"""Utility helpers for reading the latest message from the iMessage chat database.

This module purposefully keeps the implementation dependency-free (aside from the
standard library) so it can run on a bare Python installation.  The real
`chat.db` used by iMessage on macOS is a SQLite database that is usually locked
while the Messages app is open.  To keep things simple we copy the database to a
temporary file before querying it.

Usage example::

    from imessage import get_latest_message

    latest = get_latest_message()
    if latest:
        print(f"{latest.handle}: {latest.text}")

The implementation is intentionally defensive to handle the slightly different
timestamp units that Apple has used across macOS releases (seconds, milli-
seconds, micro-seconds, and nano-seconds since the Apple epoch of
2001-01-01).  The helper heuristically normalises the stored integer into a
timezone-aware ``datetime``.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
DEFAULT_DB_PATH = os.getenv(
    "IMESSAGE_DB_PATH", os.path.expanduser("~/Library/Messages/chat.db")
)


@dataclass
class IMessage:
    """Container for a single iMessage row."""

    text: Optional[str]
    handle: Optional[str]
    service: Optional[str]
    sent_at: Optional[datetime]
    is_from_me: Optional[bool]
    chat_identifier: Optional[str]
    chat_display_name: Optional[str]


def _apple_time_to_datetime(raw_value: Optional[int]) -> Optional[datetime]:
    """Convert Apple's integer timestamps into a timezone-aware ``datetime``.

    The ``message`` table stores multiple timestamp fields where the units have
    changed over time.  Historically they were stored as seconds, later as
    microseconds, and in more recent macOS releases as nanoseconds from the
    Apple epoch.  We infer the unit using the magnitude of the integer.
    """

    if not raw_value:
        return None

    absolute = abs(raw_value)
    digits = len(str(absolute))

    if digits >= 18:  # nanoseconds
        seconds = raw_value / 1_000_000_000
    elif digits >= 15:  # microseconds
        seconds = raw_value / 1_000_000
    elif digits >= 12:  # milliseconds
        seconds = raw_value / 1_000
    else:  # seconds
        seconds = float(raw_value)

    return APPLE_EPOCH + timedelta(seconds=seconds)


def _determine_db_path(db_path: Optional[str]) -> str:
    path = db_path or DEFAULT_DB_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"iMessage chat database not found at '{path}'. Set IMESSAGE_DB_PATH "
            "or pass db_path explicitly."
        )
    return path


def get_latest_message(
    chat_identifier: Optional[str] = None,
    *,
    db_path: Optional[str] = None,
    include_empty_text: bool = False,
) -> Optional[IMessage]:
    """Return the latest message optionally filtered by chat identifier.

    Args:
        chat_identifier: Optional phone number/email/handle to scope the lookup.
        db_path: Override path to ``chat.db``.  Defaults to ``IMESSAGE_DB_PATH``
            environment variable or the macOS default path.
        include_empty_text: Some rows (such as attachments or reactions) have no
            ``text`` payload.  By default these are skipped; set to ``True`` to
            consider them.

    Returns:
        ``IMessage`` instance for the most recent message or ``None`` when no
        rows match.
    """

    source_path = _determine_db_path(db_path)

    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        shutil.copy2(source_path, tmp.name)
        conn = sqlite3.connect(tmp.name)
        conn.row_factory = sqlite3.Row
        try:
            return _fetch_latest(conn, chat_identifier, include_empty_text)
        finally:
            conn.close()


def _fetch_latest(
    conn: sqlite3.Connection,
    chat_identifier: Optional[str],
    include_empty_text: bool,
) -> Optional[IMessage]:
    joins = [
        "LEFT JOIN handle ON handle.ROWID = message.handle_id",
        "LEFT JOIN chat_message_join cmj ON cmj.message_id = message.ROWID",
        "LEFT JOIN chat ON chat.ROWID = cmj.chat_id",
    ]

    where_clauses = []
    params = []

    if not include_empty_text:
        where_clauses.append("message.text IS NOT NULL AND message.text != ''")

    if chat_identifier:
        where_clauses.append(
            "(handle.id = ? OR chat.chat_identifier = ? OR chat.display_name = ?)"
        )
        params.extend([chat_identifier, chat_identifier, chat_identifier])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
        SELECT
            message.text,
            message.service,
            message.date,
            message.date_read,
            message.date_delivered,
            message.date_sent,
            message.date_ms,
            message.is_from_me,
            handle.id AS handle_id,
            chat.chat_identifier AS chat_identifier,
            chat.display_name AS chat_display_name
        FROM message
        {' '.join(joins)}
        {where_sql}
        ORDER BY
            COALESCE(message.date, message.date_sent, message.date_delivered, message.date_read, message.date_ms, 0) DESC,
            message.ROWID DESC
        LIMIT 1
    """

    cursor = conn.execute(query, params)
    row = cursor.fetchone()
    if not row:
        return None

    timestamp_fields = [
        row["date"],
        row["date_sent"],
        row["date_delivered"],
        row["date_read"],
        row["date_ms"],
    ]

    sent_at = None
    for value in timestamp_fields:
        sent_at = _apple_time_to_datetime(value)
        if sent_at:
            break

    return IMessage(
        text=row["text"],
        handle=row["handle_id"],
        service=row["service"],
        sent_at=sent_at,
        is_from_me=bool(row["is_from_me"]) if row["is_from_me"] is not None else None,
        chat_identifier=row["chat_identifier"],
        chat_display_name=row["chat_display_name"],
    )


__all__ = ["IMessage", "get_latest_message"]

