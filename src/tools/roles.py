"""roles.py — Role management tools."""

import json
import logging

import discord

from src.tools.helpers import find_member, find_role, get_guild

logger = logging.getLogger(__name__)


async def create_role(bot: discord.Client, *, role_name: str, color: str = None,
                      hoist: bool = False, mentionable: bool = False, **kwargs) -> str:
    guild = get_guild(bot)
    role_kwargs = {"name": role_name, "hoist": hoist, "mentionable": mentionable}
    if color:
        role_kwargs["color"] = discord.Color(int(color.replace("#", ""), 16))
    role = await guild.create_role(**role_kwargs)
    return json.dumps({"status": "created", "role": role.name, "id": str(role.id)})


async def delete_role(bot: discord.Client, *, role_name: str, reason: str, **kwargs) -> str:
    guild = get_guild(bot)
    role = find_role(guild, role_name)
    await role.delete(reason=reason)
    return json.dumps({"status": "deleted", "role": role_name})


async def edit_role(bot: discord.Client, *, role_name: str, new_name: str = None,
                    color: str = None, **kwargs) -> str:
    guild = get_guild(bot)
    role = find_role(guild, role_name)
    edit_kwargs = {}
    if new_name:
        edit_kwargs["name"] = new_name
    if color:
        edit_kwargs["color"] = discord.Color(int(color.replace("#", ""), 16))
    if edit_kwargs:
        await role.edit(**edit_kwargs)
    return json.dumps({"status": "edited", "role": role.name})


async def assign_role(bot: discord.Client, *, user_id: str, role_name: str, **kwargs) -> str:
    guild = get_guild(bot)
    member = await find_member(guild, user_id)
    role = find_role(guild, role_name)
    await member.add_roles(role)
    return json.dumps({"status": "assigned", "user": str(member), "role": role.name})


async def remove_role(bot: discord.Client, *, user_id: str, role_name: str, **kwargs) -> str:
    guild = get_guild(bot)
    member = await find_member(guild, user_id)
    role = find_role(guild, role_name)
    await member.remove_roles(role)
    return json.dumps({"status": "removed", "user": str(member), "role": role.name})
