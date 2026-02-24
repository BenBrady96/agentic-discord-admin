"""
config.py — Central configuration for the Agentic Discord Admin bot.

Loads environment variables from .env and exports them as typed constants.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# ─── Required Tokens ───────────────────────────────────────────────────────────
DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
ADMIN_CHANNEL_ID: int = int(os.getenv("ADMIN_CHANNEL_ID", "0"))
GUILD_ID: int = int(os.getenv("GUILD_ID", "0"))

# ─── Validate on import ────────────────────────────────────────────────────────
_REQUIRED = {
    "DISCORD_TOKEN": DISCORD_TOKEN,
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "ADMIN_CHANNEL_ID": ADMIN_CHANNEL_ID,
    "GUILD_ID": GUILD_ID,
}
for _name, _val in _REQUIRED.items():
    if not _val:
        print(f"[FATAL] Missing required environment variable: {_name}")
        print("        Copy .env.example to .env and fill in all values.")
        sys.exit(1)

# ─── Defaults ──────────────────────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", "admin_bot.db")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

# ─── Rate Limit Settings ──────────────────────────────────────────────────────
MAX_TOOL_CALLS_PER_REQUEST: int = 25      # Hard cap per user message
MAX_LOOP_ITERATIONS: int = 25             # Hard cap on ReAct while-loop
TOOL_COOLDOWN_DEFAULT: float = 1.0
TOOL_COOLDOWN_MODERATION: float = 2.0
MESSAGE_COOLDOWN: float = 2.0
CONFIRMATION_TIMEOUT: float = 60.0

# ─── Bulk Operation Caps ──────────────────────────────────────────────────────
MAX_PURGE_MESSAGES: int = 100
MAX_RECENT_MESSAGES: int = 50
MAX_SEARCH_MESSAGES: int = 25
