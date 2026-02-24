"""
helpers.py — Shared helpers for all tool modules.

Resolves Discord objects (guild, channel, role, member, category) from names/IDs.
"""

import discord

from src.config import GUILD_ID


def get_guild(bot: discord.Client) -> discord.Guild:
    """Get the configured guild the bot is managing."""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        raise ValueError(f"Guild {GUILD_ID} not found. Is the bot in the server?")
    return guild


def find_channel(guild: discord.Guild, name: str) -> discord.abc.GuildChannel:
    """Find a channel by name (case-insensitive)."""
    name_lower = name.lower().replace("#", "").strip()
    for ch in guild.channels:
        if ch.name.lower() == name_lower:
            return ch
    raise ValueError(f"Channel '{name}' not found.")


def find_role(guild: discord.Guild, name: str) -> discord.Role:
    """Find a role by name (case-insensitive)."""
    name_lower = name.lower().strip()
    for role in guild.roles:
        if role.name.lower() == name_lower:
            return role
    raise ValueError(f"Role '{name}' not found.")


def find_category(guild: discord.Guild, name: str) -> discord.CategoryChannel:
    """Find a category by name (case-insensitive)."""
    name_lower = name.lower().strip()
    for cat in guild.categories:
        if cat.name.lower() == name_lower:
            return cat
    raise ValueError(f"Category '{name}' not found.")


async def find_member(guild: discord.Guild, user_id: str) -> discord.Member:
    """Fetch a member by ID."""
    try:
        return await guild.fetch_member(int(user_id))
    except (discord.NotFound, ValueError):
        raise ValueError(f"User '{user_id}' not found in this server.")
