"""
Tests for Sepehryar Developer Copilot Engine & Multi-Stage Cognitive Reasoning.
"""
from fastapi.testclient import TestClient
from app.api.server import create_api_app
from app.agent.cognitive_engine import cognitive_engine
from app.config.settings import settings

app = create_api_app()
client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {settings.api_token}"}


def test_cognitive_engine_person_creation_reasoning():
    """Verify deep architectural reasoning for customer creation."""
    res = cognitive_engine.reason_and_solve("چطور مشتری جدید ثبت کنم و حسابش رو وصل کنم؟")
    assert "اشخاص" in res.topic or "مشتری" in res.topic
    assert any("personcod" in g for g in res.rules_and_gotchas)
    assert any("Type" in g for g in res.rules_and_gotchas)
    assert "BEGIN TRANSACTION" in res.solution_script
    assert "TblHesabText" in res.solution_script
    md = res.to_formatted_markdown()
    assert "تحلیل عمیق مهندسی" in md


def test_cognitive_engine_invoice_reasoning():
    """Verify deep architectural reasoning for invoices in TR."""
    res = cognitive_engine.reason_and_solve("چطور فاکتور فروش ثبت کنم؟")
    assert "فاکتور" in res.topic
    assert any("UpdateSiteSync" in g for g in res.rules_and_gotchas)
    assert any("(Bed + Bes)" in g for g in res.rules_and_gotchas)
    assert "dbo.TR" in res.solution_script


def test_cognitive_engine_migration_reasoning():
    """Verify reasoning for ERP data migration and polarity resolution."""
    res = cognitive_engine.reason_and_solve("چطور از باران و هلو به سپهریار مهاجرت بدم؟")
    assert "تبدیل" in res.topic or "مهاجرت" in res.topic
    assert any("قطبیت" in g for g in res.rules_and_gotchas)
    assert "def transform_to_sepehryar_person" in res.solution_script


def test_cognitive_engine_script_generation():
    """Verify transactional script synthesizer for developer scenarios."""
    # Create Person
    script_p = cognitive_engine.generate_script_for_scenario(
        "create_person",
        params={"name": "علی فکوری", "sh_ozviat": 1660, "mobile": "09138548850"}
    )
    assert "علی فکوری" in script_p["script"]
    assert "@ShOzviat INT = 1660" in script_p["script"]
    assert "personcod" in script_p["script"]

    # Trigger wrapper
    script_t = cognitive_engine.generate_script_for_scenario("disable_triggers")
    assert "DISABLE TRIGGER dbo.UpdateSiteSync_TR" in script_t["script"]
    assert "ENABLE TRIGGER dbo.UpdateSiteSync_TR" in script_t["script"]


def test_cognitive_engine_dataset_linter():
    """Verify linter catches common architectural pitfalls in proposed data."""
    bad_dataset = [
        {"name": "حسین محمودیان 09134537853", "personcod": 0, "bed": -100, "is_bank": True, "type": 1}
    ]
    report = cognitive_engine.lint_dataset("migration", bad_dataset)
    assert report["is_safe"] is False
    assert any("شماره موبایل در متن نام" in w for w in report["warnings"])
    assert any("personcod" in e for e in report["errors"])
    assert any("منفی" in e for e in report["errors"])
    assert any("حساب‌های بانکی" in e for e in report["errors"])

    clean_dataset = [
        {"name": "حسین محمودیان", "personcod": 1667, "bed": 1000000, "bes": 0, "is_bank": False, "type": 1}
    ]
    clean_report = cognitive_engine.lint_dataset("migration", clean_dataset)
    assert clean_report["is_safe"] is True


def test_copilot_rest_api_endpoints():
    """Verify Developer Copilot REST endpoints for external client tools."""
    # Ask endpoint
    res_ask = client.post(
        "/api/copilot/ask",
        headers=AUTH_HEADERS,
        json={"query": "چطور مشتری ثبت کنم؟"}
    )
    assert res_ask.status_code == 200
    data = res_ask.json()
    assert "formatted_markdown" in data
    assert len(data["rules_and_gotchas"]) > 0

    # Generate script endpoint
    res_script = client.post(
        "/api/copilot/generate-script",
        headers=AUTH_HEADERS,
        json={"scenario": "create_person", "params": {"name": "محسن کلانتری"}}
    )
    assert res_script.status_code == 200
    assert "محسن کلانتری" in res_script.json()["script"]

    # Lint data endpoint
    res_lint = client.post(
        "/api/copilot/lint-data",
        headers=AUTH_HEADERS,
        json={
            "scenario": "test",
            "dataset": [{"name": "تست 09121111111", "bed": 500}]
        }
    )
    assert res_lint.status_code == 200
    assert len(res_lint.json()["warnings"]) > 0


def test_cognitive_engine_account_definition_reasoning():
    """Verify reasoning for defining accounts and chart of accounts."""
    res = cognitive_engine.reason_and_solve("چجوری حساب تعریف بکنم")
    assert "تعریف حساب" in res.topic or "کدینگ" in res.topic
    assert any("personcod" in g for g in res.rules_and_gotchas)
    assert any("Type" in g for g in res.rules_and_gotchas)
    assert "TblPerson" in res.solution_script
    assert "Master" in res.solution_script
    assert "TblHesabText" in res.solution_script


def test_agent_orchestrator_handles_colloquial_account_definition():
    """Verify that colloquial query 'چجوری حساب تعریف بکنم' succeeds without SQL error."""
    from app.agent.orchestrator import agent_orchestrator
    resp = agent_orchestrator.process_query("چجوری حساب تعریف بکنم")
    assert resp.success is True
    assert "تعریف حساب" in resp.persian_answer or "کدینگ" in resp.persian_answer
    assert "خطا در ارتباط با دیتابیس" not in resp.persian_answer
    assert "Invalid column name" not in resp.persian_answer
