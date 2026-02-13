import sqlite3
from datetime import datetime, timezone

import pytest

from imessage import IMessage, get_latest_message


APPLE_SECONDS = int((datetime(2024, 1, 1, tzinfo=timezone.utc) - datetime(2001, 1, 1, tzinfo=timezone.utc)).total_seconds())


def _build_chat_db(path: str) -> None:
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE handle (
            ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
            id TEXT
        );
        CREATE TABLE chat (
            ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_identifier TEXT,
            display_name TEXT
        );
        CREATE TABLE message (
            ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            service TEXT,
            date INTEGER,
            date_sent INTEGER,
            date_delivered INTEGER,
            date_read INTEGER,
            date_ms INTEGER,
            is_from_me INTEGER,
            handle_id INTEGER
        );
        CREATE TABLE chat_message_join (
            chat_id INTEGER,
            message_id INTEGER
        );
        """
    )

    cur.execute("INSERT INTO handle(id) VALUES (?)", ("+15555551234",))
    handle_id = cur.lastrowid

    cur.execute(
        "INSERT INTO chat(chat_identifier, display_name) VALUES (?, ?)",
        ("group.chat", "Bagel Crew"),
    )
    chat_id = cur.lastrowid

    # Older message
    cur.execute(
        "INSERT INTO message(text, service, date, is_from_me, handle_id) VALUES (?, ?, ?, ?, ?)",
        ("Morning!", "iMessage", APPLE_SECONDS - 10, 0, handle_id),
    )
    msg1 = cur.lastrowid
    cur.execute(
        "INSERT INTO chat_message_join(chat_id, message_id) VALUES (?, ?)",
        (chat_id, msg1),
    )

    # Latest message stored in nanoseconds
    latest_ns = (APPLE_SECONDS + 5) * 1_000_000_000
    cur.execute(
        """
        INSERT INTO message(text, service, date, date_sent, date_ms, is_from_me, handle_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("Bagels are ready", "iMessage", latest_ns, latest_ns, latest_ns // 1_000_000, 1, handle_id),
    )
    msg2 = cur.lastrowid
    cur.execute(
        "INSERT INTO chat_message_join(chat_id, message_id) VALUES (?, ?)",
        (chat_id, msg2),
    )

    conn.commit()
    conn.close()


def test_get_latest_message_reads_newest_row(tmp_path):
    db_path = tmp_path / "chat.db"
    _build_chat_db(str(db_path))

    latest = get_latest_message(db_path=str(db_path))

    assert isinstance(latest, IMessage)
    assert latest.text == "Bagels are ready"
    assert latest.handle == "+15555551234"
    assert latest.chat_identifier == "group.chat"
    assert latest.chat_display_name == "Bagel Crew"
    assert latest.sent_at is not None
    assert latest.sent_at.tzinfo is timezone.utc


def test_get_latest_message_filters_by_chat_identifier(tmp_path):
    db_path = tmp_path / "chat.db"
    _build_chat_db(str(db_path))

    latest = get_latest_message(chat_identifier="Bagel Crew", db_path=str(db_path))

    assert latest is not None
    assert latest.chat_display_name == "Bagel Crew"
    assert latest.text == "Bagels are ready"


def test_get_latest_message_returns_none_when_missing(tmp_path):
    db_path = tmp_path / "chat.db"
    _build_chat_db(str(db_path))

    latest = get_latest_message(chat_identifier="unknown", db_path=str(db_path))

    assert latest is None


def test_missing_database_raises(tmp_path):
    missing = tmp_path / "missing.db"
    with pytest.raises(FileNotFoundError):
        get_latest_message(db_path=str(missing))

