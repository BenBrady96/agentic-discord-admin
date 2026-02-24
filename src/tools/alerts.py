"""alerts.py — Database alert & warning tools."""

import json
import logging

import discord

from src import database as db

logger = logging.getLogger(__name__)


async def add_alert(bot: discord.Client, *, alert_text: str, **kwargs) -> str:
    alert_id = await db.add_alert(alert_text)
    return json.dumps({"status": "added", "alert_id": alert_id})


async def get_unseen_alerts(bot: discord.Client, **kwargs) -> str:
    alerts = await db.get_unseen_alerts()
    return json.dumps(alerts)


async def mark_alert_seen(bot: discord.Client, *, alert_id: int, **kwargs) -> str:
    count = await db.mark_alerts_as_seen([alert_id])
    return json.dumps({"status": "marked_seen", "rows_affected": count})
