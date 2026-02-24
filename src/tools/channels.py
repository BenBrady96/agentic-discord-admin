"""channels.py — Channel and category management tools."""

import json
import logging

import discord

from src.tools.helpers import find_category, find_channel, find_member, find_role, get_guild

logger = logging.getLogger(__name__)


async def create_channel(bot: discord.Client, *, channel_name: str, type: str = "text",
                         category: str = None, topic: str = None, **kwargs) -> str:
    guild = get_guild(bot)
    cat = find_category(guild, category) if category else None
    if type == "voice":
        ch = await guild.create_voice_channel(channel_name, category=cat)
    elif type == "stage":
        ch = await guild.create_stage_channel(channel_name, category=cat)
    elif type == "forum":
        ch = await guild.create_forum(channel_name, category=cat, topic=topic)
    else:
        ch = await guild.create_text_channel(channel_name, category=cat, topic=topic)
    return json.dumps({"status": "created", "name": ch.name, "id": str(ch.id), "type": str(ch.type)})


async def create_category(bot: discord.Client, *, category_name: str, **kwargs) -> str:
    guild = get_guild(bot)
    cat = await guild.create_category(category_name)
    return json.dumps({"status": "created", "name": cat.name, "id": str(cat.id)})


async def edit_channel(bot: discord.Client, *, channel_name: str, new_name: str = None,
                       topic: str = None, slowmode: int = None, nsfw: bool = None, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    edit_kwargs = {}
    if new_name is not None:
        edit_kwargs["name"] = new_name
    if topic is not None and isinstance(channel, discord.TextChannel):
        edit_kwargs["topic"] = topic
    if slowmode is not None and isinstance(channel, discord.TextChannel):
        edit_kwargs["slowmode_delay"] = slowmode
    if nsfw is not None and isinstance(channel, discord.TextChannel):
        edit_kwargs["nsfw"] = nsfw
    if edit_kwargs:
        await channel.edit(**edit_kwargs)
    return json.dumps({"status": "edited", "channel": channel.name})


async def set_channel_permissions(bot: discord.Client, *, channel_name: str, target: str,
                                  allow: str = None, deny: str = None, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    try:
        target_obj = find_role(guild, target)
    except ValueError:
        target_obj = await find_member(guild, target)
    overwrite = channel.overwrites_for(target_obj)
    if allow:
        for perm_name in allow.split(","):
            perm_name = perm_name.strip()
            if hasattr(overwrite, perm_name):
                setattr(overwrite, perm_name, True)
    if deny:
        for perm_name in deny.split(","):
            perm_name = perm_name.strip()
            if hasattr(overwrite, perm_name):
                setattr(overwrite, perm_name, False)
    await channel.set_permissions(target_obj, overwrite=overwrite)
    return json.dumps({"status": "permissions_updated", "channel": channel.name, "target": str(target_obj)})


async def move_channel(bot: discord.Client, *, channel_name: str, category: str = None,
                       position: int = None, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    edit_kwargs = {}
    if category is not None:
        edit_kwargs["category"] = find_category(guild, category)
    if position is not None:
        edit_kwargs["position"] = position
    if edit_kwargs:
        await channel.edit(**edit_kwargs)
    return json.dumps({"status": "moved", "channel": channel.name})


async def delete_channel(bot: discord.Client, *, channel_name: str, reason: str, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    await channel.delete(reason=reason)
    return json.dumps({"status": "deleted", "channel": channel_name})


async def delete_category(bot: discord.Client, *, category_name: str, reason: str, **kwargs) -> str:
    guild = get_guild(bot)
    cat = find_category(guild, category_name)
    await cat.delete(reason=reason)
    return json.dumps({"status": "deleted", "category": category_name})
