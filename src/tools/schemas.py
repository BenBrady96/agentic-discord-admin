"""
schemas.py — Gemini-compatible function declarations for all admin tools.

Each schema follows the Google GenAI function calling format.
The DESTRUCTIVE_TOOLS set is used by the agentic loop to trigger
human-in-the-loop confirmation before execution.
"""

# Tools that require ✅ admin confirmation before execution
DESTRUCTIVE_TOOLS = frozenset({
    "ban_user", "unban_user", "kick_user", "timeout_user", "remove_timeout",
    "purge_messages", "delete_channel", "delete_category", "delete_role",
    "set_server_name", "delete_invite", "delete_emoji",
})


def get_all_tool_declarations() -> list[dict]:
    """Return the full list of tool declarations for the Gemini API."""
    return [
        # ─── Information & Read-Only ───────────────────────────────────
        {
            "name": "get_server_info",
            "description": "Get server details: name, owner, member count, boost level, creation date.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "list_channels",
            "description": "List all channels grouped by category with type and position.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "list_roles",
            "description": "List all roles with color, permissions summary, and member count.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "list_emojis",
            "description": "List all custom emojis and stickers in the server.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "get_user_info",
            "description": "Get user details: username, roles, join date, account age, status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The Discord user ID."},
                },
                "required": ["user_id"],
            },
        },
        {
            "name": "get_recent_messages",
            "description": "Fetch the last N messages from a channel (max 50).",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Name of the channel."},
                    "count": {"type": "integer", "description": "Number of messages to fetch (max 50)."},
                },
                "required": ["channel_name", "count"],
            },
        },
        {
            "name": "search_messages",
            "description": "Search a channel for messages containing a keyword (max 25 results).",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Name of the channel."},
                    "query": {"type": "string", "description": "Keyword to search for."},
                    "count": {"type": "integer", "description": "Max results to return (max 25)."},
                },
                "required": ["channel_name", "query"],
            },
        },
        {
            "name": "get_channel_info",
            "description": "Get channel details: topic, slowmode, NSFW flag, permissions overview.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Name of the channel."},
                },
                "required": ["channel_name"],
            },
        },
        {
            "name": "get_role_info",
            "description": "Get detailed info about a role: permissions, member list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_name": {"type": "string", "description": "Name of the role."},
                },
                "required": ["role_name"],
            },
        },
        {
            "name": "list_bans",
            "description": "List all currently banned users with reasons.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "list_invites",
            "description": "List active invite links with uses, creator, and expiry.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "get_audit_log",
            "description": "Get recent audit log entries, optionally filtered by action type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_type": {"type": "string", "description": "Optional action type filter (e.g. 'ban', 'kick', 'channel_create')."},
                    "count": {"type": "integer", "description": "Number of entries to fetch (max 50)."},
                },
                "required": [],
            },
        },
        {
            "name": "get_member_count",
            "description": "Get member counts: total, online, idle, dnd, offline.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        # ─── Messaging ────────────────────────────────────────────────
        {
            "name": "send_message",
            "description": "Send a text message to a specified channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Target channel name."},
                    "message": {"type": "string", "description": "Message content to send."},
                },
                "required": ["channel_name", "message"],
            },
        },
        {
            "name": "send_embed",
            "description": "Send a rich embed to a channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Target channel name."},
                    "title": {"type": "string", "description": "Embed title."},
                    "description": {"type": "string", "description": "Embed body text."},
                    "color": {"type": "string", "description": "Hex color code (e.g. '#FF0000'). Default blue."},
                    "fields": {"type": "string", "description": "JSON string of [{name, value, inline}] field objects."},
                },
                "required": ["channel_name", "title", "description"],
            },
        },
        {
            "name": "edit_message",
            "description": "Edit a message previously sent by the bot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Channel the message is in."},
                    "message_id": {"type": "string", "description": "ID of the message to edit."},
                    "new_content": {"type": "string", "description": "New message content."},
                },
                "required": ["channel_name", "message_id", "new_content"],
            },
        },
        {
            "name": "pin_message",
            "description": "Pin a message in a channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Channel name."},
                    "message_id": {"type": "string", "description": "ID of the message to pin."},
                },
                "required": ["channel_name", "message_id"],
            },
        },
        {
            "name": "unpin_message",
            "description": "Unpin a message in a channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Channel name."},
                    "message_id": {"type": "string", "description": "ID of the message to unpin."},
                },
                "required": ["channel_name", "message_id"],
            },
        },
        {
            "name": "create_thread",
            "description": "Create a new thread from a message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Channel containing the message."},
                    "message_id": {"type": "string", "description": "Message ID to thread from."},
                    "thread_name": {"type": "string", "description": "Name for the new thread."},
                },
                "required": ["channel_name", "message_id", "thread_name"],
            },
        },
        # ─── Channel & Category Management ────────────────────────────
        {
            "name": "create_channel",
            "description": "Create a new text, voice, stage, or forum channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Name for the new channel."},
                    "type": {"type": "string", "enum": ["text", "voice", "stage", "forum"], "description": "Channel type."},
                    "category": {"type": "string", "description": "Optional category name to place the channel under."},
                    "topic": {"type": "string", "description": "Optional channel topic/description."},
                },
                "required": ["channel_name", "type"],
            },
        },
        {
            "name": "create_category",
            "description": "Create a new channel category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_name": {"type": "string", "description": "Name for the new category."},
                },
                "required": ["category_name"],
            },
        },
        {
            "name": "edit_channel",
            "description": "Modify channel settings like name, topic, slowmode, or NSFW flag.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Current channel name."},
                    "new_name": {"type": "string", "description": "New channel name."},
                    "topic": {"type": "string", "description": "New topic."},
                    "slowmode": {"type": "integer", "description": "Slowmode delay in seconds (0 to disable)."},
                    "nsfw": {"type": "boolean", "description": "Whether to mark as NSFW."},
                },
                "required": ["channel_name"],
            },
        },
        {
            "name": "set_channel_permissions",
            "description": "Set permission overrides for a role or user on a channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Target channel."},
                    "target": {"type": "string", "description": "Role name or user ID to set permissions for."},
                    "allow": {"type": "string", "description": "Comma-separated permissions to allow (e.g. 'send_messages,read_messages')."},
                    "deny": {"type": "string", "description": "Comma-separated permissions to deny."},
                },
                "required": ["channel_name", "target"],
            },
        },
        {
            "name": "move_channel",
            "description": "Move a channel to a different category or position.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Channel to move."},
                    "category": {"type": "string", "description": "Target category name."},
                    "position": {"type": "integer", "description": "New position index."},
                },
                "required": ["channel_name"],
            },
        },
        {
            "name": "delete_channel",
            "description": "⚠️ DESTRUCTIVE: Delete a channel permanently.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Channel to delete."},
                    "reason": {"type": "string", "description": "Reason for deletion."},
                },
                "required": ["channel_name", "reason"],
            },
        },
        {
            "name": "delete_category",
            "description": "⚠️ DESTRUCTIVE: Delete a category. Channels inside are orphaned, not deleted.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_name": {"type": "string", "description": "Category to delete."},
                    "reason": {"type": "string", "description": "Reason for deletion."},
                },
                "required": ["category_name", "reason"],
            },
        },
        # ─── Moderation ───────────────────────────────────────────────
        {
            "name": "ban_user",
            "description": "⚠️ DESTRUCTIVE: Ban a user from the server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID to ban."},
                    "reason": {"type": "string", "description": "Reason for the ban."},
                    "delete_days": {"type": "integer", "description": "Days of message history to delete (0-7). Default 0."},
                },
                "required": ["user_id", "reason"],
            },
        },
        {
            "name": "unban_user",
            "description": "⚠️ DESTRUCTIVE: Revoke a ban for a user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID to unban."},
                    "reason": {"type": "string", "description": "Reason for unbanning."},
                },
                "required": ["user_id", "reason"],
            },
        },
        {
            "name": "kick_user",
            "description": "⚠️ DESTRUCTIVE: Kick a user from the server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID to kick."},
                    "reason": {"type": "string", "description": "Reason for the kick."},
                },
                "required": ["user_id", "reason"],
            },
        },
        {
            "name": "timeout_user",
            "description": "⚠️ DESTRUCTIVE: Timeout (mute) a user for a specified duration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID to timeout."},
                    "duration_minutes": {"type": "integer", "description": "Timeout duration in minutes (max 40320 = 28 days)."},
                    "reason": {"type": "string", "description": "Reason for the timeout."},
                },
                "required": ["user_id", "duration_minutes", "reason"],
            },
        },
        {
            "name": "remove_timeout",
            "description": "⚠️ DESTRUCTIVE: Remove a timeout from a user early.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID to un-timeout."},
                    "reason": {"type": "string", "description": "Reason for removing timeout."},
                },
                "required": ["user_id", "reason"],
            },
        },
        {
            "name": "purge_messages",
            "description": "⚠️ DESTRUCTIVE: Bulk-delete messages from a channel (max 100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Channel to purge from."},
                    "count": {"type": "integer", "description": "Number of messages to delete (max 100)."},
                    "reason": {"type": "string", "description": "Reason for purging."},
                },
                "required": ["channel_name", "count", "reason"],
            },
        },
        {
            "name": "warn_user",
            "description": "Send a warning DM to a user and log it to the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID to warn."},
                    "reason": {"type": "string", "description": "Reason for the warning."},
                },
                "required": ["user_id", "reason"],
            },
        },
        # ─── Role Management ──────────────────────────────────────────
        {
            "name": "create_role",
            "description": "Create a new server role.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_name": {"type": "string", "description": "Name for the new role."},
                    "color": {"type": "string", "description": "Hex color (e.g. '#FF5733'). Default none."},
                    "hoist": {"type": "boolean", "description": "Display separately in member list. Default false."},
                    "mentionable": {"type": "boolean", "description": "Allow anyone to @mention. Default false."},
                },
                "required": ["role_name"],
            },
        },
        {
            "name": "delete_role",
            "description": "⚠️ DESTRUCTIVE: Delete a role from the server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_name": {"type": "string", "description": "Role name to delete."},
                    "reason": {"type": "string", "description": "Reason for deletion."},
                },
                "required": ["role_name", "reason"],
            },
        },
        {
            "name": "edit_role",
            "description": "Modify a role's name, color, or other properties.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_name": {"type": "string", "description": "Current role name."},
                    "new_name": {"type": "string", "description": "New role name."},
                    "color": {"type": "string", "description": "New hex color."},
                },
                "required": ["role_name"],
            },
        },
        {
            "name": "assign_role",
            "description": "Add a role to a user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID."},
                    "role_name": {"type": "string", "description": "Role name to assign."},
                },
                "required": ["user_id", "role_name"],
            },
        },
        {
            "name": "remove_role",
            "description": "Remove a role from a user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID."},
                    "role_name": {"type": "string", "description": "Role name to remove."},
                },
                "required": ["user_id", "role_name"],
            },
        },
        # ─── Server Settings ──────────────────────────────────────────
        {
            "name": "set_server_name",
            "description": "⚠️ DESTRUCTIVE: Rename the server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_name": {"type": "string", "description": "New server name."},
                },
                "required": ["new_name"],
            },
        },
        {
            "name": "set_slowmode",
            "description": "Set slowmode delay on a channel (0 to disable).",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Target channel."},
                    "seconds": {"type": "integer", "description": "Slowmode delay in seconds."},
                },
                "required": ["channel_name", "seconds"],
            },
        },
        {
            "name": "set_channel_topic",
            "description": "Update a channel's topic/description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Target channel."},
                    "topic": {"type": "string", "description": "New topic text."},
                },
                "required": ["channel_name", "topic"],
            },
        },
        {
            "name": "lock_channel",
            "description": "Lock a channel by denying @everyone send_messages permission.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Channel to lock."},
                    "reason": {"type": "string", "description": "Reason for locking."},
                },
                "required": ["channel_name"],
            },
        },
        {
            "name": "unlock_channel",
            "description": "Unlock a channel by restoring @everyone send_messages permission.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Channel to unlock."},
                    "reason": {"type": "string", "description": "Reason for unlocking."},
                },
                "required": ["channel_name"],
            },
        },
        # ─── Invite Management ────────────────────────────────────────
        {
            "name": "create_invite",
            "description": "Create an invite link for a channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string", "description": "Channel to create invite for."},
                    "max_age": {"type": "integer", "description": "Invite expiry in seconds (0 = never). Default 86400."},
                    "max_uses": {"type": "integer", "description": "Max uses (0 = unlimited). Default 0."},
                    "temporary": {"type": "boolean", "description": "Grant temporary membership. Default false."},
                },
                "required": ["channel_name"],
            },
        },
        {
            "name": "delete_invite",
            "description": "⚠️ DESTRUCTIVE: Revoke an invite link.",
            "parameters": {
                "type": "object",
                "properties": {
                    "invite_code": {"type": "string", "description": "The invite code to revoke."},
                    "reason": {"type": "string", "description": "Reason for revoking."},
                },
                "required": ["invite_code", "reason"],
            },
        },
        # ─── Emoji & Sticker ─────────────────────────────────────────
        {
            "name": "create_emoji",
            "description": "Upload a custom emoji from a URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emoji_name": {"type": "string", "description": "Name for the emoji (alphanumeric + underscores)."},
                    "image_url": {"type": "string", "description": "URL of the image to upload."},
                },
                "required": ["emoji_name", "image_url"],
            },
        },
        {
            "name": "delete_emoji",
            "description": "⚠️ DESTRUCTIVE: Delete a custom emoji.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emoji_name": {"type": "string", "description": "Name of the emoji to delete."},
                    "reason": {"type": "string", "description": "Reason for deletion."},
                },
                "required": ["emoji_name", "reason"],
            },
        },
        # ─── Database / Alerts ────────────────────────────────────────
        {
            "name": "add_alert",
            "description": "Insert a system alert into the database for the daily summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "alert_text": {"type": "string", "description": "Alert text to store."},
                },
                "required": ["alert_text"],
            },
        },
        {
            "name": "get_unseen_alerts",
            "description": "Retrieve all unseen system alerts from the database.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "mark_alert_seen",
            "description": "Mark a specific alert as seen by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "alert_id": {"type": "integer", "description": "The alert ID to mark as seen."},
                },
                "required": ["alert_id"],
            },
        },
    ]
