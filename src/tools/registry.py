"""
registry.py — Central TOOL_REGISTRY mapping tool names to functions.

Each domain module registers its own functions here.
"""

from src.tools.info import (
    get_audit_log,
    get_channel_info,
    get_member_count,
    get_recent_messages,
    get_role_info,
    get_server_info,
    get_user_info,
    list_bans,
    list_channels,
    list_emojis,
    list_invites,
    list_roles,
    search_messages,
)
from src.tools.messaging import (
    create_thread,
    edit_message,
    pin_message,
    send_embed,
    send_message,
    unpin_message,
)
from src.tools.channels import (
    create_category,
    create_channel,
    delete_category,
    delete_channel,
    edit_channel,
    move_channel,
    set_channel_permissions,
)
from src.tools.moderation import (
    ban_user,
    kick_user,
    purge_messages,
    remove_timeout,
    timeout_user,
    unban_user,
    warn_user,
)
from src.tools.roles import (
    assign_role,
    create_role,
    delete_role,
    edit_role,
    remove_role,
)
from src.tools.server import (
    lock_channel,
    set_channel_topic,
    set_server_name,
    set_slowmode,
    unlock_channel,
)
from src.tools.invites import create_invite, delete_invite
from src.tools.emoji import create_emoji, delete_emoji
from src.tools.alerts import add_alert, get_unseen_alerts, mark_alert_seen


TOOL_REGISTRY: dict[str, callable] = {
    # ── Information & Read-Only ──
    "get_server_info": get_server_info,
    "list_channels": list_channels,
    "list_roles": list_roles,
    "list_emojis": list_emojis,
    "get_user_info": get_user_info,
    "get_recent_messages": get_recent_messages,
    "search_messages": search_messages,
    "get_channel_info": get_channel_info,
    "get_role_info": get_role_info,
    "list_bans": list_bans,
    "list_invites": list_invites,
    "get_audit_log": get_audit_log,
    "get_member_count": get_member_count,
    # ── Messaging ──
    "send_message": send_message,
    "send_embed": send_embed,
    "edit_message": edit_message,
    "pin_message": pin_message,
    "unpin_message": unpin_message,
    "create_thread": create_thread,
    # ── Channel & Category ──
    "create_channel": create_channel,
    "create_category": create_category,
    "edit_channel": edit_channel,
    "set_channel_permissions": set_channel_permissions,
    "move_channel": move_channel,
    "delete_channel": delete_channel,
    "delete_category": delete_category,
    # ── Moderation ──
    "ban_user": ban_user,
    "unban_user": unban_user,
    "kick_user": kick_user,
    "timeout_user": timeout_user,
    "remove_timeout": remove_timeout,
    "purge_messages": purge_messages,
    "warn_user": warn_user,
    # ── Roles ──
    "create_role": create_role,
    "delete_role": delete_role,
    "edit_role": edit_role,
    "assign_role": assign_role,
    "remove_role": remove_role,
    # ── Server Settings ──
    "set_server_name": set_server_name,
    "set_slowmode": set_slowmode,
    "set_channel_topic": set_channel_topic,
    "lock_channel": lock_channel,
    "unlock_channel": unlock_channel,
    # ── Invites ──
    "create_invite": create_invite,
    "delete_invite": delete_invite,
    # ── Emoji ──
    "create_emoji": create_emoji,
    "delete_emoji": delete_emoji,
    # ── Database / Alerts ──
    "add_alert": add_alert,
    "get_unseen_alerts": get_unseen_alerts,
    "mark_alert_seen": mark_alert_seen,
}
