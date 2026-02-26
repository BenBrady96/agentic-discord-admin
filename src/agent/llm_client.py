"""
llm_client.py — Gemini-powered ReAct (Reason + Act) engine.

Implements the agentic loop:
  1. Send user message + conversation history to Gemini with tool declarations.
  2. If Gemini returns tool calls → execute them (or pause for destructive ones).
  3. Feed tool results back into the conversation and loop.
  4. When Gemini returns plain text → yield it as the final response.
  5. Rate limiting and hard caps prevent runaway API usage.
"""

import asyncio
import json
import logging
import re
from typing import AsyncGenerator, Union

import discord
from google import genai
from google.genai import types

from src.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MAX_LOOP_ITERATIONS,
    MAX_TOOL_CALLS_PER_REQUEST,
)
from src.rate_limiter import RateLimiter
from src.tools import DESTRUCTIVE_TOOLS, TOOL_REGISTRY, get_all_tool_declarations
from src.agent.events import ConfirmationRequest, FinalResponse, StatusUpdate

logger = logging.getLogger(__name__)

# ─── Retry settings for 429 / RESOURCE_EXHAUSTED ─────────────────────────────
MAX_RETRIES = 3
BASE_RETRY_DELAY = 30.0 


# ─── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an expert Discord server administrator assistant. You help manage \
the server by using the tools available to you.

## How you operate:
1. **Be fully autonomous** — ALWAYS use your tools to look up information. \
   NEVER ask the admin for information you can fetch with a tool. \
   You have tools for everything: get_user_info, list_channels, list_roles, etc. \
   USE THEM. Do not ask the user to provide data you can look up yourself.
2. **Think step-by-step** — reason about what you need, then act immediately.
3. **Chain multiple tool calls** — for multi-step tasks, gather data first, \
   then execute each action. You CAN call multiple tools in sequence. \
   Do not tell the user "I can only do X one at a time" — just DO them.
4. **Be cautious with destructive actions** — these require admin confirmation.
5. **Handle errors gracefully** — if a tool fails, retry or try an alternative.

## Workflow examples:
- "Delete all channels with 'bingo' in the name" → call list_channels, \
  filter results for channels containing 'bingo', then call delete_channel \
  for EACH matching channel.
- "Remove all roles from user X" → call get_user_info to see their roles, \
  then call remove_role for EACH role (skip @everyone).
- "Who joined in the last week?" → call get_member_count or list members.
- "Find messages about X in #general" → call search_messages.
- "Warn whoever said 'something offensive' in #general" → call search_messages \
  with channel_name="general" and query="something offensive", get the author_id \
  from the results, then call warn_user with that user_id.

## Important rules:
- NEVER ask the user for data you can look up with a tool. Just look it up.
- You CAN call the same tool multiple times with different arguments.
- When given a keyword like "bingo", search/filter tool results yourself.
- Summarise results concisely — don't dump raw JSON at the user.
- Respect rate limits — don't make unnecessary API calls.
"""


def _parse_retry_delay(error_text: str) -> float:
    """Try to extract the suggested retry delay from a 429 error message."""
    match = re.search(r"retry in ([\d.]+)s", str(error_text), re.IGNORECASE)
    if match:
        return float(match.group(1))
    return BASE_RETRY_DELAY


# ─── Agent ────────────────────────────────────────────────────────────────────

class GeminiAgent:
    """
    Wraps the Google GenAI client and implements the ReAct agentic loop.

    Usage:
        agent = GeminiAgent(bot)
        async for event in agent.run("Ban the spammer"):
            if isinstance(event, ConfirmationRequest):
                ...  # ask admin for ✅, then set event.approved
            elif isinstance(event, FinalResponse):
                ...  # post event.text to the channel
    """

    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot
        self.rate_limiter = RateLimiter()
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.last_messages: list[types.Content] = []  # full conversation from last run

        raw_declarations = get_all_tool_declarations()
        self.tool_declarations = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(**decl) for decl in raw_declarations
            ]
        )

    async def run(
        self,
        user_message: str,
        conversation_history: list[types.Content] | None = None,
    ) -> AsyncGenerator[Union[ConfirmationRequest, FinalResponse, StatusUpdate], None]:
        """The core ReAct loop. Yields events for the caller to handle."""

        messages: list[types.Content] = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append(
            types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
        )

        tool_call_count = 0
        iteration = 0

        while iteration < MAX_LOOP_ITERATIONS:
            iteration += 1

            # ── Call Gemini with automatic retry on 429 ───────────────
            response = None
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = await self.client.aio.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=messages,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            tools=[self.tool_declarations],
                            temperature=0.2,
                        ),
                    )
                    break  # success
                except Exception as e:
                    error_str = str(e)
                    is_rate_limit = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str

                    if is_rate_limit and attempt < MAX_RETRIES:
                        delay = _parse_retry_delay(error_str) + (attempt * 2)
                        logger.warning(
                            f"Rate limited (attempt {attempt}/{MAX_RETRIES}). "
                            f"Retrying in {delay:.1f}s..."
                        )
                        yield StatusUpdate(
                            text=f"⏳ Rate limited by Gemini — retrying in 30s "
                                 f"(attempt {attempt}/{MAX_RETRIES})..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Gemini API error: {e}")
                        yield FinalResponse(text=f"❌ LLM error: {e}")
                        self.last_messages = messages
                        return

            if response is None:
                self.last_messages = messages
                yield FinalResponse(text="❌ Failed to get a response from Gemini after retries.")
                return

            candidate = response.candidates[0] if response.candidates else None
            if not candidate or not candidate.content or not candidate.content.parts:
                self.last_messages = messages
                yield FinalResponse(text="⚠️ Empty response from LLM.")
                return

            messages.append(candidate.content)

            function_calls = [p for p in candidate.content.parts if p.function_call]
            text_parts = [p for p in candidate.content.parts if p.text]

            if not function_calls:
                final_text = "\n".join(p.text for p in text_parts if p.text)
                self.last_messages = messages
                yield FinalResponse(text=final_text or "✅ Done.")
                return

            # ── Process tool calls ────────────────────────────────────
            function_responses = []

            for part in function_calls:
                fc = part.function_call
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}

                tool_call_count += 1
                if tool_call_count > MAX_TOOL_CALLS_PER_REQUEST:
                    logger.warning("Tool call limit reached.")
                    function_responses.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"error": "Tool call limit reached for this request."},
                        )
                    )
                    continue

                await self.rate_limiter.acquire(tool_name)

                # Destructive action → ask for confirmation
                if tool_name in DESTRUCTIVE_TOOLS:
                    yield StatusUpdate(text=f"🔒 Requesting approval for **{tool_name}**...")
                    confirmation = ConfirmationRequest(tool_name=tool_name, tool_args=tool_args)
                    yield confirmation

                    if not confirmation.approved:
                        function_responses.append(
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"error": "Action was rejected by admin."},
                            )
                        )
                        continue

                # Execute the tool
                yield StatusUpdate(text=f"⚙️ Running `{tool_name}`...")
                tool_fn = TOOL_REGISTRY.get(tool_name)
                if not tool_fn:
                    function_responses.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"error": f"Unknown tool: {tool_name}"},
                        )
                    )
                    continue

                try:
                    result = await tool_fn(self.bot, **tool_args)
                    result_data = json.loads(result) if isinstance(result, str) else result
                    # Gemini FunctionResponse requires a dict — wrap lists
                    result_dict = result_data if isinstance(result_data, dict) else {"result": result_data}
                    function_responses.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response=result_dict,
                        )
                    )
                except Exception as e:
                    logger.error(f"Tool '{tool_name}' failed: {e}")
                    function_responses.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"error": str(e)},
                        )
                    )

            messages.append(types.Content(role="user", parts=function_responses))

        self.last_messages = messages
        yield FinalResponse(text="⚠️ Maximum reasoning steps reached. Please try a simpler request.")
