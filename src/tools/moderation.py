"""moderation.py — Moderation tools (ban, kick, timeout, purge, warn)."""

import json
import logging
from datetime import timedelta

import discord

from src.config import MAX_PURGE_MESSAGES
from src.tools.helpers import find_channel, find_member, get_guild
from src import database as db

logger = logging.getLogger(__name__)


async def ban_user(bot: discord.Client, *, user_id: str, reason: str, delete_days: int = 0, **kwargs) -> str:
    guild = get_guild(bot)
    member = await find_member(guild, user_id)
    delete_days = min(max(delete_days, 0), 7)
    await guild.ban(member, reason=reason, delete_message_seconds=delete_days * 86400)
    return json.dumps({"status": "banned", "user": str(member), "reason": reason})


async def unban_user(bot: discord.Client, *, user_id: str, reason: str, **kwargs) -> str:
    guild = get_guild(bot)
    user = await bot.fetch_user(int(user_id))
    await guild.unban(user, reason=reason)
    return json.dumps({"status": "unbanned", "user": str(user), "reason": reason})


async def kick_user(bot: discord.Client, *, user_id: str, reason: str, **kwargs) -> str:
    guild = get_guild(bot)
    member = await find_member(guild, user_id)
    await member.kick(reason=reason)
    return json.dumps({"status": "kicked", "user": str(member), "reason": reason})


async def timeout_user(bot: discord.Client, *, user_id: str, duration_minutes: int, reason: str, **kwargs) -> str:
    guild = get_guild(bot)
    member = await find_member(guild, user_id)
    duration_minutes = min(duration_minutes, 40320)  # 28 days max
    until = discord.utils.utcnow() + timedelta(minutes=duration_minutes)
    await member.timeout(until, reason=reason)
    return json.dumps({"status": "timed_out", "user": str(member), "until": until.isoformat(), "reason": reason})


async def remove_timeout(bot: discord.Client, *, user_id: str, reason: str, **kwargs) -> str:
    guild = get_guild(bot)
    member = await find_member(guild, user_id)
    await member.timeout(None, reason=reason)
    return json.dumps({"status": "timeout_removed", "user": str(member), "reason": reason})


async def purge_messages(bot: discord.Client, *, channel_name: str, count: int, reason: str, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": f"'{channel_name}' is not a text channel."})
    count = min(count, MAX_PURGE_MESSAGES)
    deleted = await channel.purge(limit=count, reason=reason)
    return json.dumps({"status": "purged", "count": len(deleted), "channel": channel_name})


async def warn_user(bot: discord.Client, *, user_id: str, reason: str, **kwargs) -> str:
    guild = get_guild(bot)
    member = await find_member(guild, user_id)
    warning_id = await db.add_warning(user_id, reason, str(bot.user))
    try:
        await member.send(f"⚠️ **Warning from {guild.name}:** {reason}")
        dm_sent = True
    except (discord.Forbidden, discord.HTTPException):
        dm_sent = False
    return json.dumps({
        "status": "warned", "user": str(member), "reason": reason,
        "warning_id": warning_id, "dm_sent": dm_sent,
    })
