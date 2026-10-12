"""
Tests for Sepehryar AI Core Brain REST API endpoints (/api/brain/*).
"""
from fastapi.testclient import TestClient
from app.api.server import create_api_app
from app.config.settings import settings

app = create_api_app()
client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {settings.api_token}"}


def test_api_brain_list_agents():
    """Verify GET /api/brain/agents returns registered specialized agents."""
    resp = client.get("/api/brain/agents", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_agents"] == 7
    roles = [a["role"] for a in data["agents"]]
    assert "database" in roles
    assert "sql" in roles
    assert "procedure" in roles
    assert "code" in roles
    assert "debug" in roles
    assert "architecture" in roles
    assert "critic" in roles


def test_api_brain_solve_endpoint():
    """Verify POST /api/brain/solve returns full multi-agent coordinated reasoning."""
    payload = {
        "query": "یک Stored Procedure استاندارد برای انبارداری و کنترل موجودی کالا بنویس",
        "session_id": "test_session_1",
        "database": "DEMO"
    }
    resp = client.post("/api/brain/solve", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["critic_verdict"] in ("approved", "approved_with_warnings")
    assert len(data["sub_agents_used"]) > 0
    assert len(data["reasoning_steps"]) > 0
    assert data["generated_sp"] is not None


def test_api_brain_direct_agent_endpoint():
    """Verify POST /api/brain/agents/database dispatches task directly to DatabaseAgent."""
    payload = {
        "goal": "بررسی روابط جدول TblPerson و Master",
        "context": {}
    }
    resp = client.post("/api/brain/agents/database", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "database"
    assert data["success"] is True
    assert len(data["findings"]) > 0
