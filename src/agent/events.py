"""
events.py — Data classes yielded by the agentic loop.

Separated from llm_client.py to avoid circular imports and keep
the agent module's public API clean.
"""

from dataclasses import dataclass


@dataclass
class ConfirmationRequest:
    """Yielded when a destructive tool call needs admin approval."""
    tool_name: str
    tool_args: dict
    approved: bool = False


@dataclass
class FinalResponse:
    """Yielded when the LLM produces a final text response."""
    text: str


@dataclass
class StatusUpdate:
    """Yielded to show the user what the bot is currently doing."""
    text: str
