"""info.py — Read-only information-gathering tools."""

import json
import logging

import discord

from src.config import MAX_RECENT_MESSAGES, MAX_SEARCH_MESSAGES
from src.tools.helpers import find_channel, find_role, get_guild, find_member

logger = logging.getLogger(__name__)

AUDIT_ACTION_MAP = {
    "ban": discord.AuditLogAction.ban,
    "unban": discord.AuditLogAction.unban,
    "kick": discord.AuditLogAction.kick,
    "channel_create": discord.AuditLogAction.channel_create,
    "channel_delete": discord.AuditLogAction.channel_delete,
    "role_create": discord.AuditLogAction.role_create,
    "role_delete": discord.AuditLogAction.role_delete,
    "message_delete": discord.AuditLogAction.message_delete,
}


async def get_server_info(bot: discord.Client, **kwargs) -> str:
    guild = get_guild(bot)
    return json.dumps({
        "name": guild.name,
        "id": str(guild.id),
        "owner": str(guild.owner),
        "member_count": guild.member_count,
        "boost_level": guild.premium_tier,
        "boost_count": guild.premium_subscription_count,
        "created_at": guild.created_at.isoformat(),
        "text_channels": len(guild.text_channels),
        "voice_channels": len(guild.voice_channels),
        "categories": len(guild.categories),
        "roles": len(guild.roles),
        "emojis": len(guild.emojis),
    })


async def list_channels(bot: discord.Client, **kwargs) -> str:
    guild = get_guild(bot)
    result = {}
    for category in guild.categories:
        result[category.name] = [
            {"name": ch.name, "type": str(ch.type), "id": str(ch.id)}
            for ch in category.channels
        ]
    uncategorized = [
        {"name": ch.name, "type": str(ch.type), "id": str(ch.id)}
        for ch in guild.channels
        if ch.category is None and not isinstance(ch, discord.CategoryChannel)
    ]
    if uncategorized:
        result["(no category)"] = uncategorized
    return json.dumps(result)


async def list_roles(bot: discord.Client, **kwargs) -> str:
    guild = get_guild(bot)
    roles = [
        {
            "name": r.name, "id": str(r.id), "color": str(r.color),
            "members": len(r.members), "position": r.position,
            "mentionable": r.mentionable, "hoist": r.hoist,
        }
        for r in sorted(guild.roles, key=lambda r: r.position, reverse=True)
    ]
    return json.dumps(roles)


async def list_emojis(bot: discord.Client, **kwargs) -> str:
    guild = get_guild(bot)
    emojis = [
        {"name": e.name, "id": str(e.id), "animated": e.animated, "url": str(e.url)}
        for e in guild.emojis
    ]
    return json.dumps(emojis)


async def get_user_info(bot: discord.Client, *, user_id: str, **kwargs) -> str:
    guild = get_guild(bot)
    member = await find_member(guild, user_id)
    return json.dumps({
        "name": str(member),
        "display_name": member.display_name,
        "id": str(member.id),
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "created_at": member.created_at.isoformat(),
        "roles": [r.name for r in member.roles if r.name != "@everyone"],
        "top_role": member.top_role.name,
        "status": str(member.status) if hasattr(member, "status") else "unknown",
        "bot": member.bot,
    })


async def get_recent_messages(bot: discord.Client, *, channel_name: str, count: int, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": f"'{channel_name}' is not a text channel."})
    count = min(count, MAX_RECENT_MESSAGES)
    messages = []
    async for msg in channel.history(limit=count):
        messages.append({
            "author": str(msg.author),
            "content": msg.content[:500],
            "timestamp": msg.created_at.isoformat(),
            "id": str(msg.id),
            "attachments": [a.url for a in msg.attachments],
        })
    return json.dumps(messages)


async def search_messages(bot: discord.Client, *, channel_name: str, query: str, count: int = 25, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": f"'{channel_name}' is not a text channel."})
    count = min(count, MAX_SEARCH_MESSAGES)
    query_lower = query.lower()
    results = []
    async for msg in channel.history(limit=500):
        if query_lower in msg.content.lower():
            results.append({
                "author": str(msg.author),
                "content": msg.content[:500],
                "timestamp": msg.created_at.isoformat(),
                "id": str(msg.id),
            })
            if len(results) >= count:
                break
    return json.dumps(results)


async def get_channel_info(bot: discord.Client, *, channel_name: str, **kwargs) -> str:
    guild = get_guild(bot)
    channel = find_channel(guild, channel_name)
    info = {
        "name": channel.name, "id": str(channel.id), "type": str(channel.type),
        "category": channel.category.name if channel.category else None,
        "position": channel.position, "created_at": channel.created_at.isoformat(),
    }
    if isinstance(channel, discord.TextChannel):
        info.update({
            "topic": channel.topic,
            "slowmode_delay": channel.slowmode_delay,
            "nsfw": channel.is_nsfw(),
        })
    return json.dumps(info)


async def get_role_info(bot: discord.Client, *, role_name: str, **kwargs) -> str:
    guild = get_guild(bot)
    role = find_role(guild, role_name)
    perms = [p for p, v in role.permissions if v]
    members = [str(m) for m in role.members[:50]]
    return json.dumps({
        "name": role.name, "id": str(role.id), "color": str(role.color),
        "position": role.position, "hoist": role.hoist,
        "mentionable": role.mentionable,
        "permissions": perms,
        "member_count": len(role.members),
        "members_sample": members,
    })


async def list_bans(bot: discord.Client, **kwargs) -> str:
    guild = get_guild(bot)
    bans = []
    async for entry in guild.bans(limit=100):
        bans.append({
            "user": str(entry.user), "id": str(entry.user.id),
            "reason": entry.reason,
        })
    return json.dumps(bans)


async def list_invites(bot: discord.Client, **kwargs) -> str:
    guild = get_guild(bot)
    invites = await guild.invites()
    return json.dumps([
        {
            "code": inv.code, "url": inv.url,
            "creator": str(inv.inviter) if inv.inviter else "Unknown",
            "uses": inv.uses, "max_uses": inv.max_uses,
            "expires_at": inv.expires_at.isoformat() if inv.expires_at else "Never",
            "channel": inv.channel.name if inv.channel else "Unknown",
        }
        for inv in invites
    ])


async def get_audit_log(bot: discord.Client, *, action_type: str = None, count: int = 20, **kwargs) -> str:
    guild = get_guild(bot)
    action = AUDIT_ACTION_MAP.get(action_type) if action_type else None
    count = min(count, 50)
    entries = []
    async for entry in guild.audit_logs(limit=count, action=action):
        entries.append({
            "action": str(entry.action),
            "user": str(entry.user),
            "target": str(entry.target),
            "reason": entry.reason,
            "created_at": entry.created_at.isoformat(),
        })
    return json.dumps(entries)


async def get_member_count(bot: discord.Client, **kwargs) -> str:
    guild = get_guild(bot)
    total = guild.member_count or 0
    online = sum(1 for m in guild.members if hasattr(m, "status") and str(m.status) == "online")
    idle = sum(1 for m in guild.members if hasattr(m, "status") and str(m.status) == "idle")
    dnd = sum(1 for m in guild.members if hasattr(m, "status") and str(m.status) == "dnd")
    offline = total - online - idle - dnd
    return json.dumps({
        "total": total, "online": online, "idle": idle, "dnd": dnd, "offline": offline,
    })
