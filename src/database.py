"""
database.py — Async SQLite database layer.

Uses a persistent shared connection so all operations hit the same database.
"""

import aiosqlite

from src.config import DB_PATH

# ─── Shared connection ────────────────────────────────────────────────────────
_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """Return the shared database connection, creating it on first call."""
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
    return _db


async def close_db() -> None:
    """Close the shared connection (call on shutdown)."""
    global _db
    if _db:
        await _db.close()
        _db = None


async def init_db() -> None:
    """Create tables if they don't already exist."""
    db = await get_db()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS system_alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_text  TEXT    NOT NULL,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_seen     BOOLEAN  DEFAULT 0
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT    NOT NULL,
            reason      TEXT    NOT NULL,
            warned_by   TEXT    NOT NULL,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await db.commit()


# ─── System Alerts ─────────────────────────────────────────────────────────────

async def add_alert(alert_text: str) -> int:
    """Insert a new system alert. Returns the new row ID."""
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO system_alerts (alert_text) VALUES (?)", (alert_text,),
    )
    await db.commit()
    return cursor.lastrowid


async def get_unseen_alerts() -> list[dict]:
    """Retrieve all unseen alerts regardless of date."""
    db = await get_db()
    async with db.execute(
        "SELECT id, alert_text, timestamp FROM system_alerts "
        "WHERE is_seen = 0 ORDER BY timestamp ASC"
    ) as cursor:
        return [dict(row) for row in await cursor.fetchall()]


async def get_unseen_alerts_for_date(date_str: str) -> list[dict]:
    """Retrieve unseen alerts for a specific date (YYYY-MM-DD)."""
    db = await get_db()
    async with db.execute(
        "SELECT id, alert_text, timestamp FROM system_alerts "
        "WHERE is_seen = 0 AND DATE(timestamp) = ? ORDER BY timestamp ASC",
        (date_str,),
    ) as cursor:
        return [dict(row) for row in await cursor.fetchall()]


async def mark_alerts_as_seen(alert_ids: list[int]) -> int:
    """Bulk-update alerts to is_seen = 1. Returns rows affected."""
    if not alert_ids:
        return 0
    placeholders = ",".join("?" for _ in alert_ids)
    db = await get_db()
    cursor = await db.execute(
        f"UPDATE system_alerts SET is_seen = 1 WHERE id IN ({placeholders})",
        alert_ids,
    )
    await db.commit()
    return cursor.rowcount


# ─── Warnings ──────────────────────────────────────────────────────────────────

async def add_warning(user_id: str, reason: str, warned_by: str) -> int:
    """Insert a user warning. Returns the new row ID."""
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO warnings (user_id, reason, warned_by) VALUES (?, ?, ?)",
        (user_id, reason, warned_by),
    )
    await db.commit()
    return cursor.lastrowid


async def get_warnings_for_user(user_id: str) -> list[dict]:
    """Retrieve all warnings for a specific user."""
    db = await get_db()
    async with db.execute(
        "SELECT id, reason, warned_by, timestamp FROM warnings "
        "WHERE user_id = ? ORDER BY timestamp DESC",
        (user_id,),
    ) as cursor:
        return [dict(row) for row in await cursor.fetchall()]
