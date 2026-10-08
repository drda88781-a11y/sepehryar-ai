"""
Tests for ChatMemoryManager session management and message persistence in SQLite.
"""
from app.agent.memory import chat_memory


def test_chat_memory_session_and_messages():
    """Verify session creation and appending conversation turns."""
    session_id = chat_memory.create_session(title="تست گفت‌وگو", database_context="DEMO")
    assert session_id is not None

    chat_memory.add_message(session_id, "user", "سلام موجودی چقدره؟")
    chat_memory.add_message(session_id, "assistant", "موجودی انبار مرکزی بررسی شد.")

    messages = chat_memory.get_messages(session_id)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

    sessions = chat_memory.list_sessions()
    assert any(s["id"] == session_id for s in sessions)
