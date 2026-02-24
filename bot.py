"""
bot.py — Entry point for the Agentic Discord Admin bot.

Handles:
  - Discord event listeners (on_ready, on_message)
  - Admin role permission guard
  - Human-in-the-loop confirmation flow for destructive actions
  - Midnight scheduled task for daily alert summaries
  - Conversation context management
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands
from google import genai
from google.genai import types

from src import database as db
from src.agent import GeminiAgent, ConfirmationRequest, FinalResponse, StatusUpdate
from src.config import (
    ADMIN_CHANNEL_ID,
    CONFIRMATION_TIMEOUT,
    DISCORD_TOKEN,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MESSAGE_COOLDOWN,
)

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("bot")

# ─── Bot setup ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Per-channel conversation history for context persistence
conversation_history: dict[int, list] = {}
MAX_HISTORY_TURNS = 20

# Cooldown tracking
_last_message_time: float = 0.0

# Agent instance (created after bot is ready)
agent: GeminiAgent | None = None


# ─── Permission check ────────────────────────────────────────────────────────

def _is_admin(member: discord.Member) -> bool:
    """Return True if the member has administrator permissions."""
    return member.guild_permissions.administrator


# ─── Events ──────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    """Initialise database, agent, and scheduler when the bot connects."""
    global agent

    logger.info(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"🔒 Listening only in channel ID: {ADMIN_CHANNEL_ID}")

    await db.init_db()
    logger.info("📦 Database initialised.")

    agent = GeminiAgent(bot)
    logger.info("🤖 Gemini agent ready.")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        midnight_alert_summary,
        CronTrigger(hour=0, minute=0),
        id="midnight_alerts",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("⏰ Midnight alert scheduler started.")


@bot.event
async def on_message(message: discord.Message):
    """
    Main message handler — the gateway into the agentic loop.

    Guards:
      1. Ignore bot messages (prevents infinite loops)
      2. Ignore DMs
      3. Ignore any channel that isn't ADMIN_CHANNEL_ID
      4. Reject non-admin users with a visible warning
    """
    global _last_message_time

    if message.author.bot:
        return
    if not message.guild:
        return
    if message.channel.id != ADMIN_CHANNEL_ID:
        return

    # ── Admin role guard ──────────────────────────────────────────
    if not _is_admin(message.author):
        await message.channel.send(
            f"🚫 {message.author.mention}, you need the **Administrator** permission to use this bot."
        )
        logger.warning(f"Non-admin {message.author} attempted to use the bot.")
        return

    # ── Cooldown between messages ─────────────────────────────────
    now = asyncio.get_event_loop().time()
    if now - _last_message_time < MESSAGE_COOLDOWN:
        remaining = MESSAGE_COOLDOWN - (now - _last_message_time)
        await asyncio.sleep(remaining)
    _last_message_time = asyncio.get_event_loop().time()

    logger.info(f"📨 Message from {message.author}: {message.content[:100]}")

    async with message.channel.typing():
        await handle_agent_request(message)


# ─── Agentic Loop Handler ────────────────────────────────────────────────────

async def handle_agent_request(message: discord.Message):
    """Run the ReAct loop for a user message."""
    channel = message.channel
    channel_id = channel.id
    history = conversation_history.get(channel_id, [])
    status_msg: discord.Message | None = None

    try:
        async for event in agent.run(message.content, history):
            if isinstance(event, StatusUpdate):
                if status_msg:
                    try:
                        await status_msg.edit(content=event.text)
                    except discord.HTTPException:
                        status_msg = await channel.send(event.text)
                else:
                    status_msg = await channel.send(event.text)

            elif isinstance(event, ConfirmationRequest):
                await handle_confirmation(channel, message.author, event)

            elif isinstance(event, FinalResponse):
                if status_msg:
                    try:
                        await status_msg.delete()
                    except discord.HTTPException:
                        pass
                text = event.text or "✅ Done."
                for chunk in split_message(text):
                    await channel.send(chunk)

    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        await channel.send(f"❌ An error occurred: {e}")

    # Persist full conversation context (user + model + tool results)
    full_messages = agent.last_messages if agent else []
    if full_messages:
        # Trim to keep history manageable
        if len(full_messages) > MAX_HISTORY_TURNS * 2:
            full_messages = full_messages[-(MAX_HISTORY_TURNS * 2):]
        conversation_history[channel_id] = full_messages


async def handle_confirmation(
    channel: discord.TextChannel,
    requester: discord.User,
    confirmation: ConfirmationRequest,
):
    """Post a confirmation embed with ✅/❌ buttons for a destructive action."""
    embed = discord.Embed(
        title="🔒 Confirmation Required",
        description="The bot wants to execute a **destructive action**.",
        color=discord.Color.red(),
    )
    embed.add_field(name="Action", value=f"`{confirmation.tool_name}`", inline=False)
    embed.add_field(
        name="Parameters",
        value=f"```json\n{json.dumps(confirmation.tool_args, indent=2)}\n```",
        inline=False,
    )
    embed.add_field(
        name="How to respond",
        value="Click **Approve** or **Reject** below.",
        inline=False,
    )
    embed.set_footer(text=f"Requested by {requester} • Expires in {int(CONFIRMATION_TIMEOUT)}s")

    # ── Button view ───────────────────────────────────────────────
    result_event = asyncio.Event()

    class ConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=CONFIRMATION_TIMEOUT)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            """Only allow server admins to click the buttons."""
            member = interaction.guild.get_member(interaction.user.id)
            if member and _is_admin(member):
                return True
            await interaction.response.send_message(
                "🚫 Only administrators can approve or reject this.", ephemeral=True
            )
            return False

        async def on_timeout(self):
            confirmation.approved = False
            embed.set_footer(text="⏰ Timed out — action cancelled.")
            self.clear_items()
            try:
                await confirm_msg.edit(embed=embed, view=self)
            except discord.HTTPException:
                pass
            result_event.set()

        @discord.ui.button(label="Approve", style=discord.ButtonStyle.green, emoji="✅")
        async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
            confirmation.approved = True
            embed.set_footer(text=f"✅ Approved by {interaction.user}")
            self.clear_items()
            await interaction.response.edit_message(embed=embed, view=self)
            logger.info(f"Destructive action '{confirmation.tool_name}' approved by {interaction.user}")
            self.stop()
            result_event.set()

        @discord.ui.button(label="Reject", style=discord.ButtonStyle.red, emoji="❌")
        async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
            confirmation.approved = False
            embed.set_footer(text=f"❌ Rejected by {interaction.user}")
            self.clear_items()
            await interaction.response.edit_message(embed=embed, view=self)
            logger.info(f"Destructive action '{confirmation.tool_name}' rejected by {interaction.user}")
            self.stop()
            result_event.set()

    view = ConfirmView()
    confirm_msg = await channel.send(embed=embed, view=view)
    await result_event.wait()


# ─── Midnight Alert Summary ──────────────────────────────────────────────────

async def midnight_alert_summary():
    """Fetch yesterday's unseen alerts, LLM-format a summary, post to admin channel."""
    logger.info("🌙 Running midnight alert summary...")

    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    alerts = await db.get_unseen_alerts_for_date(yesterday)

    if not alerts:
        logger.info("No unseen alerts for yesterday. Skipping.")
        return

    alert_text = "\n".join(f"- [{a['timestamp']}] {a['alert_text']}" for a in alerts)
    prompt = (
        f"Here are the system alerts from yesterday ({yesterday}) that haven't been "
        f"reviewed yet. Format them into a clean, concise daily summary with priorities "
        f"noted:\n\n{alert_text}"
    )

    client = genai.Client(api_key=GEMINI_API_KEY)
    try:
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a server admin assistant. Format the given alerts into "
                    "a clean daily summary. Use markdown formatting. Be concise."
                ),
                temperature=0.3,
            ),
        )
        summary_text = response.text or "No summary generated."
    except Exception as e:
        logger.error(f"LLM error during midnight summary: {e}")
        summary_text = f"**⚠️ Raw alerts (LLM formatting failed):**\n{alert_text}"

    admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if not admin_channel:
        logger.error(f"Admin channel {ADMIN_CHANNEL_ID} not found!")
        return

    embed = discord.Embed(
        title=f"🌙 Daily Alert Summary — {yesterday}",
        description=summary_text[:4000],
        color=discord.Color.dark_gold(),
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text=f"{len(alerts)} alert(s) processed")
    await admin_channel.send(embed=embed)

    alert_ids = [a["id"] for a in alerts]
    await db.mark_alerts_as_seen(alert_ids)
    logger.info(f"✅ Midnight summary posted. {len(alerts)} alerts marked as seen.")


# ─── Utilities ────────────────────────────────────────────────────────────────

def split_message(text: str, limit: int = 2000) -> list[str]:
    """Split a long message into chunks that fit Discord's character limit."""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN, log_handler=None)
