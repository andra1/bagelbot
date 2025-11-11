import os
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional

APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
DEFAULT_DB_PATH = Path.home() / "Library/Messages/chat.db"


class IMessageError(RuntimeError):
    """Raised when the iMessage history database cannot be queried."""


def _resolve_db_path(override: Optional[str]) -> Path:
    env_override = os.getenv("IMESSAGE_DB_PATH")
    target = Path(override or env_override or DEFAULT_DB_PATH)
    target = target.expanduser().resolve()
    if not target.exists():
        raise IMessageError(f"iMessage database not found at {target}")
    return target


def _apple_time_to_datetime(raw_value: Optional[int]) -> Optional[datetime]:
    """Convert Apple's Core Data timestamp to a timezone-aware datetime."""
    if raw_value is None:
        return None

    seconds = float(raw_value)
    # Apple stores timestamps as seconds (legacy) or nanoseconds (Big Sur+).
    if seconds > 1e18:
        seconds /= 1e9
    elif seconds > 1e15:
        seconds /= 1e9
    elif seconds > 1e12:
        seconds /= 1e6
    elif seconds > 1e10:
        seconds /= 1e3

    return APPLE_EPOCH + timedelta(seconds=seconds)


@dataclass
class IMessage:
    guid: str
    sender: Optional[str]
    text: Optional[str]
    sent_at: Optional[datetime]
    is_from_me: bool
    service: Optional[str]

    def to_dict(self):
        data = asdict(self)
        if self.sent_at:
            data["sent_at"] = self.sent_at.astimezone(timezone.utc).isoformat()
        return data


class IMessageReader:
    """Simple helper for querying messages from the macOS Messages database."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = _resolve_db_path(db_path)

    def _connect(self):
        return sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

    def list_chats(self, limit: int = 50) -> List[dict]:
        """Return a list of recent chats with their identifiers."""
        sql = """
        SELECT guid, chat_identifier, display_name, last_addressed_handle, last_read_message_timestamp
        FROM chat
        ORDER BY COALESCE(last_read_message_timestamp, 0) DESC, guid DESC
        LIMIT ?
        """
        with self._connect() as conn:
            cursor = conn.execute(sql, (limit,))
            rows = cursor.fetchall()
        chats = []
        for guid, identifier, display_name, last_handle, timestamp in rows:
            chats.append({
                "guid": guid,
                "identifier": identifier,
                "display_name": display_name or identifier,
                "last_addressed_handle": last_handle,
                "last_read_timestamp": _apple_time_to_datetime(timestamp).isoformat() if timestamp else None,
            })
        return chats

    def fetch_messages(
        self,
        chat_identifier: str,
        limit: int = 50,
        direction: str = "desc",
    ) -> List[IMessage]:
        """Fetch the most recent messages for the given chat identifier."""
        if direction not in {"asc", "desc"}:
            raise ValueError("direction must be 'asc' or 'desc'")

        sql = f"""
        SELECT
            message.guid,
            message.text,
            message.date,
            message.is_from_me,
            message.service,
            handle.id as handle
        FROM chat
        JOIN chat_message_join cmj ON cmj.chat_id = chat.ROWID
        JOIN message ON message.ROWID = cmj.message_id
        LEFT JOIN handle ON handle.ROWID = message.handle_id
        WHERE chat.chat_identifier = ?
        ORDER BY message.date {'ASC' if direction == 'asc' else 'DESC'}
        LIMIT ?
        """

        with self._connect() as conn:
            cursor = conn.execute(sql, (chat_identifier, limit))
            rows = cursor.fetchall()

        messages: List[IMessage] = []
        for guid, text, raw_date, is_from_me, service, handle in rows:
            messages.append(
                IMessage(
                    guid=guid,
                    sender=handle if not is_from_me else "me",
                    text=text,
                    sent_at=_apple_time_to_datetime(raw_date),
                    is_from_me=bool(is_from_me),
                    service=service,
                )
            )
        return messages

    def fetch_latest_for_handles(
        self,
        handles: Iterable[str],
        per_handle_limit: int = 5,
    ) -> dict:
        """Fetch messages for multiple handles and return a dict keyed by handle."""
        result = {}
        for handle in handles:
            chats = self._chat_identifiers_for_handle(handle)
            if not chats:
                result[handle] = []
                continue
            # use the first chat identifier for the handle.
            result[handle] = [
                msg.to_dict()
                for msg in self.fetch_messages(chats[0], per_handle_limit, direction="desc")
            ]
        return result

    def _chat_identifiers_for_handle(self, handle: str) -> List[str]:
        sql = """
        SELECT DISTINCT chat.chat_identifier
        FROM chat
        JOIN chat_handle_join chj ON chj.chat_id = chat.ROWID
        JOIN handle ON handle.ROWID = chj.handle_id
        WHERE handle.id = ?
        """
        with self._connect() as conn:
            cursor = conn.execute(sql, (handle,))
            rows = cursor.fetchall()
        return [row[0] for row in rows]
    
    def read_messages_from_person(self, handle: str, limit: int = 50) -> List[IMessage]:
        """fetch messages from a specific person by their handle."""
        chats = self._chat_identifiers_for_handle(handle)
        if not chats:
            print("didn't find any chats for handle:", handle)
            return []
        # use the first chat identifier for the handle.
        return self.fetch_messages(chats[0], limit, direction="desc")


if __name__ == "__main__":
    reader = IMessageReader()
    # chats = reader.list_chats(limit=10)
    # for chat in chats:
    #     print(chat)
    messages = reader.fetch_messages(chat_identifier="+18338192348", limit=10)
    for msg in messages:
        print(msg.to_dict())
    # vinaya_chats = reader.read_messages_from_person(handle="+16303624283", limit=5)
    # for msg in vinaya_chats:
    #     print(msg.to_dict())