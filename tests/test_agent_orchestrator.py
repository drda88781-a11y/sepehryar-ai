"""
Tests for Agent Orchestrator cognitive pipeline and intent planning.
"""
from app.agent.orchestrator import agent_orchestrator
from app.agent.planner import task_planner
from app.agent.schemas import UserIntent


def test_intent_detection():
    """Verify natural language classification into structured intents."""
    res1 = task_planner.detect_intent("تعداد کل کالاها در انبار چقدر است؟")
    assert res1.intent == UserIntent.DATABASE_QUERY
    assert "TblKala" in res1.extracted_entities

    res2 = task_planner.detect_intent("ارتباط جدول TblKala با TR چیست؟")
    assert res2.intent == UserIntent.SCHEMA_INSPECTION

    res3 = task_planner.detect_intent("چرا به SQL وصل نمیشه و خطای سرویس میده؟")
    assert res3.intent == UserIntent.TROUBLESHOOTING

    res4 = task_planner.detect_intent("وضعیت مصرف رم و پردازنده سرور چطوره؟")
    assert res4.intent == UserIntent.SYSTEM_HEALTH


def test_orchestrator_database_query_execution():
    """Verify end-to-end processing of database count query."""
    res = agent_orchestrator.process_query("تعداد کالاها چقدره؟", database_name="DEMO")
    assert res.success is True
    assert res.intent == UserIntent.DATABASE_QUERY
    assert res.sql_plan is not None
    assert "TblKala" in res.sql_plan.generated_sql
    assert res.sql_result is not None
    assert len(res.tools_used) > 0
    assert res.tools_used[0].tool_name == "run_safe_select"
    assert "رکورد" in res.persian_answer or "TblKala" in res.persian_answer


def test_orchestrator_relationships_query():
    """Verify relationship explanation query."""
    res = agent_orchestrator.process_query("ارتباط TblKala با TR چیه؟", database_name="DEMO")
    assert res.success is True
    assert res.intent == UserIntent.SCHEMA_INSPECTION
    assert len(res.persian_answer) > 0
