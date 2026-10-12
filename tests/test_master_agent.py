"""
Tests for Sepehryar AI Core Master Agent, orchestration loop, and Critic gatekeeping.
"""
from app.agent.master_agent import master_agent, MasterAgentResponse
from app.agent.specialized import CriticVerdict, AgentRole


def test_master_agent_procedure_generation():
    """Verify Master Agent coordinates Database, Architecture, Procedure, Code, and Critic agents."""
    query = "یک Stored Procedure برای ثبت سند حسابداری با کنترل تراز بنویس"
    res: MasterAgentResponse = master_agent.solve(query)

    assert res.success is True
    assert res.query == query
    assert len(res.reasoning_steps) >= 4
    # Check that Procedure was generated
    assert res.generated_sp is not None
    assert "CREATE PROCEDURE" in res.generated_sp
    assert "BEGIN TRANSACTION" in res.generated_sp
    assert "COMMIT TRANSACTION" in res.generated_sp
    # Check that C# code was generated
    assert res.generated_code is not None
    assert "SqlConnection" in res.generated_code
    # Check Critic evaluation
    assert res.critic_review is not None
    assert res.critic_review.verdict in (CriticVerdict.APPROVED, CriticVerdict.APPROVED_WITH_WARNINGS)
    assert len(res.critic_review.safety_checks) > 0


def test_master_agent_root_cause_analysis():
    """Verify Master Agent diagnoses accounting and database errors with RCA chain."""
    query = "خطای عدم تراز در سند افتتاحیه به دلیل اختلاف sum(bed) و sum(bes)"
    res: MasterAgentResponse = master_agent.solve(query)

    assert res.success is True
    assert "debug" in res.sub_agent_results
    debug_result = res.sub_agent_results["debug"]
    assert "ریشه اصلی" in debug_result.summary or len(debug_result.findings) > 0
    assert any("TblSanad" in f or "Bed" in f or "تراز" in f for f in debug_result.findings)


def test_master_agent_beyond_kb_hypotheses():
    """Verify Deductive Reasoning generates hypotheses beyond canned knowledge."""
    query = "محاسبه مانده آنلاین مشتری و گردش حساب"
    res: MasterAgentResponse = master_agent.solve(query)

    assert res.success is True
    assert "Beyond-KB" in res.solution_markdown or "فرضیه‌" in res.solution_markdown
    assert res.critic_review is not None
    assert res.critic_review.architecture_compatibility is True
