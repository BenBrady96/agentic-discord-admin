"""messaging.py — Message sending/editing/pinning tools."""

import json
import logging

import discord

from src.tools.helpers import find_channel, get_guild

logger = logging.getLogger(__name__)


async def send_message(bot: discord.Client, *, channel_name: str, message: str, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": f"'{channel_name}' is not a text channel."})
    msg = await channel.send(message)
    return json.dumps({"status": "sent", "message_id": str(msg.id)})


async def send_embed(bot: discord.Client, *, channel_name: str, title: str, description: str,
                     color: str = "#3498db", fields: str = None, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": f"'{channel_name}' is not a text channel."})
    hex_color = int(color.replace("#", ""), 16)
    embed = discord.Embed(title=title, description=description, color=hex_color)
    if fields:
        try:
            for field in json.loads(fields):
                embed.add_field(
                    name=field.get("name", "—"),
                    value=field.get("value", "—"),
                    inline=field.get("inline", False),
                )
        except (json.JSONDecodeError, TypeError):
            pass
    msg = await channel.send(embed=embed)
    return json.dumps({"status": "sent", "message_id": str(msg.id)})


async def edit_message(bot: discord.Client, *, channel_name: str, message_id: str, new_content: str, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": f"'{channel_name}' is not a text channel."})
    try:
        msg = await channel.fetch_message(int(message_id))
        if msg.author != bot.user:
            return json.dumps({"error": "Can only edit messages sent by the bot."})
        await msg.edit(content=new_content)
        return json.dumps({"status": "edited", "message_id": str(msg.id)})
    except discord.NotFound:
        return json.dumps({"error": f"Message {message_id} not found."})


async def pin_message(bot: discord.Client, *, channel_name: str, message_id: str, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": f"'{channel_name}' is not a text channel."})
    msg = await channel.fetch_message(int(message_id))
    await msg.pin()
    return json.dumps({"status": "pinned", "message_id": str(msg.id)})


async def unpin_message(bot: discord.Client, *, channel_name: str, message_id: str, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": f"'{channel_name}' is not a text channel."})
    msg = await channel.fetch_message(int(message_id))
    await msg.unpin()
    return json.dumps({"status": "unpinned", "message_id": str(msg.id)})


async def create_thread(bot: discord.Client, *, channel_name: str, message_id: str, thread_name: str, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": f"'{channel_name}' is not a text channel."})
    msg = await channel.fetch_message(int(message_id))
    thread = await msg.create_thread(name=thread_name)
    return json.dumps({"status": "created", "thread_name": thread.name, "thread_id": str(thread.id)})
