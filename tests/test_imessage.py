import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from imessage import IMessageReader


def _apple_seconds(dt: datetime) -> int:
    delta = dt.astimezone(timezone.utc) - APPLE_EPOCH
    return int(delta.total_seconds())


def _prepare_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "chat.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT);
            CREATE TABLE chat (
                ROWID INTEGER PRIMARY KEY,
                guid TEXT,
                chat_identifier TEXT,
                display_name TEXT,
                last_read_message_timestamp INTEGER
            );
            CREATE TABLE message (
                ROWID INTEGER PRIMARY KEY,
                guid TEXT,
                text TEXT,
                date INTEGER,
                is_from_me INTEGER,
                handle_id INTEGER,
                service TEXT
            );
            CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER);
            CREATE TABLE chat_handle_join (chat_id INTEGER, handle_id INTEGER);
            """
        )
        conn.execute("INSERT INTO handle (ROWID, id) VALUES (?, ?)", (1, "+15551234567"))
        conn.execute(
            "INSERT INTO chat (ROWID, guid, chat_identifier, display_name, last_read_message_timestamp) VALUES (?, ?, ?, ?, ?)",
            (1, "chat1", "+15551234567", "Alice", _apple_seconds(datetime(2024, 1, 1, tzinfo=timezone.utc))),
        )
        conn.execute("INSERT INTO chat_handle_join (chat_id, handle_id) VALUES (?, ?)", (1, 1))

        first_msg_time = _apple_seconds(datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc))
        second_msg_time = _apple_seconds(datetime(2024, 1, 1, 12, 5, tzinfo=timezone.utc))
        conn.execute(
            "INSERT INTO message (ROWID, guid, text, date, is_from_me, handle_id, service) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (100, "msg-100", "First", first_msg_time, 0, 1, "iMessage"),
        )
        conn.execute(
            "INSERT INTO message (ROWID, guid, text, date, is_from_me, handle_id, service) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (101, "msg-101", "Second", second_msg_time, 1, 1, "iMessage"),
        )
        conn.execute("INSERT INTO chat_message_join (chat_id, message_id) VALUES (?, ?)", (1, 100))
        conn.execute("INSERT INTO chat_message_join (chat_id, message_id) VALUES (?, ?)", (1, 101))
        conn.commit()
    return db_path


def test_fetch_messages_returns_entries(tmp_path):
    db_path = _prepare_db(tmp_path)
    reader = IMessageReader(db_path=str(db_path))

    result = reader.fetch_messages("+15551234567", limit=5)
    assert len(result) == 2
    assert result[0].text == "Second"
    assert result[0].is_from_me is True
    assert result[0].sender == "me"
    assert result[1].sender == "+15551234567"


def test_list_chats_includes_metadata(tmp_path):
    db_path = _prepare_db(tmp_path)
    reader = IMessageReader(db_path=str(db_path))

    chats = reader.list_chats()
    assert chats[0]["identifier"] == "+15551234567"
    assert chats[0]["display_name"] == "Alice"
    assert chats[0]["last_read_timestamp"].endswith("+00:00")


def test_fetch_latest_for_handles_returns_dict(tmp_path):
    db_path = _prepare_db(tmp_path)
    reader = IMessageReader(db_path=str(db_path))

    payload = reader.fetch_latest_for_handles(["+15551234567"])
    assert "+15551234567" in payload
    assert payload["+15551234567"][0]["text"] == "Second"
