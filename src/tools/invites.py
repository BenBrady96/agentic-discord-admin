"""invites.py — Invite management tools."""

import json
import logging

import discord

from src.tools.helpers import find_channel, get_guild

logger = logging.getLogger(__name__)


async def create_invite(bot: discord.Client, *, channel_name: str, max_age: int = 86400,
                        max_uses: int = 0, temporary: bool = False, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    invite = await channel.create_invite(max_age=max_age, max_uses=max_uses, temporary=temporary)
    return json.dumps({"status": "created", "url": invite.url, "code": invite.code})


async def delete_invite(bot: discord.Client, *, invite_code: str, reason: str, **kwargs) -> str:
    invite = await bot.fetch_invite(invite_code)
    await invite.delete(reason=reason)
    return json.dumps({"status": "deleted", "invite_code": invite_code})
