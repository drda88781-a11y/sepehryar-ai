"""
Chat session and conversation memory manager backed by local SQLite.
Ensures context window size is maintained and conversation history is persisted safely.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from app.core.logger import get_logger
from app.storage.sqlite import sqlite_manager

logger = get_logger("memory")


class ChatMemoryManager:
    """Manages chat sessions and conversation turns in SQLite."""

    def __init__(self, manager=sqlite_manager) -> None:
        self.manager = manager

    def create_session(self, title: str = "گفت‌وگوی جدید", database_context: Optional[str] = None) -> str:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.manager.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chat_sessions (id, title, created_at, updated_at, database_context, messages_json)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (session_id, title, now, now, database_context or "", json.dumps([], ensure_ascii=False))
            )
        return session_id

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """Append a message turn (user or assistant) to a session."""
        now = datetime.now(timezone.utc).isoformat()
        with self.manager.get_connection() as conn:
            row = conn.execute("SELECT messages_json FROM chat_sessions WHERE id = ?;", (session_id,)).fetchone()
            if not row:
                messages = []
                is_new = True
            else:
                is_new = False
                try:
                    messages = json.loads(row["messages_json"])
                except Exception:
                    messages = []

            turn = {
                "role": role,
                "content": content,
                "timestamp": now,
                "metadata": metadata or {}
            }
            messages.append(turn)

            # Cap recent context to last 20 messages
            if len(messages) > 20:
                messages = messages[-20:]

            json_str = json.dumps(messages, ensure_ascii=False)
            if is_new:
                title = content[:50].replace("\n", " ").strip() or "گفت‌وگوی جدید"
                conn.execute(
                    """
                    INSERT INTO chat_sessions (id, title, created_at, updated_at, database_context, messages_json)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (session_id, title, now, now, "", json_str)
                )
            else:
                conn.execute(
                    "UPDATE chat_sessions SET messages_json = ?, updated_at = ? WHERE id = ?;",
                    (json_str, now, session_id)
                )

    def get_messages(self, session_id: str) -> list[dict[str, Any]]:
        """Retrieve recent messages for a session."""
        with self.manager.get_connection() as conn:
            row = conn.execute("SELECT messages_json FROM chat_sessions WHERE id = ?;", (session_id,)).fetchone()
            if row and row["messages_json"]:
                try:
                    return json.loads(row["messages_json"])
                except Exception:
                    return []
            return []

    def list_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent conversation sessions."""
        with self.manager.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, title, created_at, updated_at, database_context
                FROM chat_sessions
                ORDER BY updated_at DESC
                LIMIT ?;
                """,
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]


chat_memory = ChatMemoryManager()
