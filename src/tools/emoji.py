"""emoji.py — Emoji and sticker tools."""

import json
import logging

import aiohttp
import discord

from src.tools.helpers import get_guild

logger = logging.getLogger(__name__)


async def create_emoji(bot: discord.Client, *, emoji_name: str, image_url: str, **kwargs) -> str:
    guild = get_guild(bot)
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            if resp.status != 200:
                return json.dumps({"error": f"Failed to download image: HTTP {resp.status}"})
            image_data = await resp.read()
    emoji = await guild.create_custom_emoji(name=emoji_name, image=image_data)
    return json.dumps({"status": "created", "emoji": str(emoji), "name": emoji.name})


async def delete_emoji(bot: discord.Client, *, emoji_name: str, reason: str, **kwargs) -> str:
    guild = get_guild(bot)
    emoji = discord.utils.get(guild.emojis, name=emoji_name)
    if not emoji:
        return json.dumps({"error": f"Emoji '{emoji_name}' not found."})
    await emoji.delete(reason=reason)
    return json.dumps({"status": "deleted", "emoji": emoji_name})
