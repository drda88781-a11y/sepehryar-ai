"""
Tests for local REST API endpoints, security authentication, and request handling.
"""
import pytest
from fastapi import HTTPException
from app.api.models import (
    ChatApiRequest,
    SQLQueryApiRequest,
    ExportApiRequest,
)
from app.api.routes import (
    get_health,
    search_knowledge,
    chat_with_agent,
    execute_readonly_sql,
    export_data_endpoint,
)
from app.api.security import verify_loopback_client
from app.config.settings import settings


class MockClient:
    def __init__(self, host: str):
        self.host = host

class MockRequest:
    def __init__(self, host: str = "127.0.0.1", headers: dict = None):
        self.client = MockClient(host)
        self.headers = headers or {}


def test_api_health_endpoint():
    res = get_health()
    assert res.status == "ok"
    assert res.version == settings.app_version
    assert res.offline_strict == settings.offline_strict


def test_api_loopback_security_blocks_remote():
    # Loopback request passes
    req_local = MockRequest(host="127.0.0.1")
    verify_loopback_client(req_local)

    # Remote public IP raises 403 Forbidden
    req_remote = MockRequest(host="185.190.20.5")
    with pytest.raises(HTTPException) as exc_info:
        verify_loopback_client(req_remote)
    assert exc_info.value.status_code == 403


def test_api_search_knowledge():
    res = search_knowledge(q="بانک", limit=3)
    assert res.query == "بانک"
    assert res.total_found > 0
    assert len(res.results) > 0


def test_api_chat_with_agent():
    req = ChatApiRequest(query="سلام، چه کارهایی می‌توانی انجام دهی؟")
    res = chat_with_agent(req)
    assert res.success is True
    assert len(res.persian_answer) > 0
    assert res.duration_ms > 0
    assert isinstance(res.reasoning_steps, list)
    assert len(res.reasoning_steps) > 0
    assert res.thinking_duration_ms > 0


def test_api_chat_thinking_modes():
    # 1. Fast mode
    req_fast = ChatApiRequest(query="سلام", thinking_mode="fast")
    res_fast = chat_with_agent(req_fast)
    assert res_fast.success is True
    assert res_fast.thinking_duration_ms > 0

    # 2. Deep Audit mode
    req_deep = ChatApiRequest(query="تحلیل تراز افتتاحیه و مانده اشخاص", thinking_mode="deep")
    res_deep = chat_with_agent(req_deep)
    assert res_deep.success is True
    assert res_deep.thinking_mode == "deep"
    assert len(res_deep.reasoning_steps) >= 3
    assert res_deep.critic_verdict is not None


def test_api_chat_stream_thinking_events():
    from app.agent.orchestrator import agent_orchestrator
    
    # Balanced mode
    events = list(agent_orchestrator.stream_process_query(query="سلام"))
    thinking_steps = [e for e in events if isinstance(e, dict) and e.get("type") == "thinking_step"]
    thinking_dones = [e for e in events if isinstance(e, dict) and e.get("type") == "thinking_done"]
    assert len(thinking_steps) > 0
    assert len(thinking_dones) == 1
    assert thinking_dones[0]["duration_ms"] > 0

    # Deep Audit mode streams 5 specialized audit steps
    events_deep = list(agent_orchestrator.stream_process_query(query="بررسی مغایرت حساب اشخاص", thinking_mode="deep"))
    deep_steps = [e for e in events_deep if isinstance(e, dict) and e.get("type") == "thinking_step"]
    assert len(deep_steps) >= 5
    assert any("کاوش" in s.get("title", "") or "Schema" in s.get("title", "") for s in deep_steps)


def test_api_sql_execute_readonly():
    from app.database.connection import db_connection_manager
    db_connection_manager.set_connection_state(True)
    try:
        req = SQLQueryApiRequest(sql="SELECT 1 AS num", max_rows=5)
        res = execute_readonly_sql(req)
        assert res.columns == ["num"]
        assert len(res.rows) == 1
        assert res.rows[0]["num"] == 1
    finally:
        db_connection_manager.set_connection_state(False)


def test_api_sql_blocks_dangerous_mutation():
    req = SQLQueryApiRequest(sql="DROP TABLE TblKala")
    with pytest.raises(HTTPException) as exc_info:
        execute_readonly_sql(req)
    assert exc_info.value.status_code == 400


def test_api_export_endpoint():
    rows = [{"id": 1, "item": "کالای آزمایشی"}]
    req = ExportApiRequest(format="csv", filename="api_test.csv", rows=rows)
    res = export_data_endpoint(req)
    assert res.success is True
    assert res.total_rows == 1
    assert res.format == "csv"
