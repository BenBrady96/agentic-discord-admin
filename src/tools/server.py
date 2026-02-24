"""server.py — Server settings tools."""

import json
import logging

import discord

from src.tools.helpers import find_channel, get_guild

logger = logging.getLogger(__name__)


async def set_server_name(bot: discord.Client, *, new_name: str, **kwargs) -> str:
    guild = get_guild(bot)
    old_name = guild.name
    await guild.edit(name=new_name)
    return json.dumps({"status": "renamed", "old_name": old_name, "new_name": new_name})


async def set_slowmode(bot: discord.Client, *, channel_name: str, seconds: int, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": f"'{channel_name}' is not a text channel."})
    await channel.edit(slowmode_delay=seconds)
    return json.dumps({"status": "slowmode_set", "channel": channel.name, "seconds": seconds})


async def set_channel_topic(bot: discord.Client, *, channel_name: str, topic: str, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": f"'{channel_name}' is not a text channel."})
    await channel.edit(topic=topic)
    return json.dumps({"status": "topic_set", "channel": channel.name, "topic": topic})


async def lock_channel(bot: discord.Client, *, channel_name: str, reason: str = None, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    everyone = guild.default_role
    await channel.set_permissions(everyone, send_messages=False, reason=reason)
    return json.dumps({"status": "locked", "channel": channel.name})


async def unlock_channel(bot: discord.Client, *, channel_name: str, reason: str = None, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    everyone = guild.default_role
    await channel.set_permissions(everyone, send_messages=None, reason=reason)
    return json.dumps({"status": "unlocked", "channel": channel.name})
