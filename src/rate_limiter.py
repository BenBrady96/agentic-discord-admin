"""
rate_limiter.py — Proactive rate-limit protection.

Prevents the autonomous LLM loop from hitting Discord API rate limits
by enforcing per-tool cooldowns with async semaphore + sleep.
"""

import asyncio
import logging
import time

from src.config import TOOL_COOLDOWN_DEFAULT, TOOL_COOLDOWN_MODERATION

logger = logging.getLogger(__name__)

MODERATION_TOOLS = frozenset({
    "ban_user", "unban_user", "kick_user", "timeout_user", "remove_timeout",
    "purge_messages", "delete_channel", "delete_category", "delete_role",
    "set_server_name", "delete_invite", "delete_emoji",
})


class RateLimiter:
    """Async-safe rate limiter that enforces per-tool cooldowns."""

    def __init__(self) -> None:
        self._last_call: dict[str, float] = {}
        self._global_lock = asyncio.Lock()

    def _get_cooldown(self, tool_name: str) -> float:
        if tool_name in MODERATION_TOOLS:
            return TOOL_COOLDOWN_MODERATION
        return TOOL_COOLDOWN_DEFAULT

    async def acquire(self, tool_name: str) -> None:
        """Wait until the cooldown for this tool has elapsed."""
        async with self._global_lock:
            cooldown = self._get_cooldown(tool_name)
            now = time.monotonic()
            elapsed = now - self._last_call.get(tool_name, 0.0)
            if elapsed < cooldown:
                wait_time = cooldown - elapsed
                logger.debug(f"Rate limiter: waiting {wait_time:.2f}s for '{tool_name}'")
                await asyncio.sleep(wait_time)
            self._last_call[tool_name] = time.monotonic()

    def reset(self) -> None:
        """Clear all tracked cooldowns."""
        self._last_call.clear()
