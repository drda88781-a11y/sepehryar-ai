"""
Tests for Smart Cognitive Engine:
- MarketOntologyParser (Bazaar terms & Persian semantics)
- GoldenPatternsEngine (Pre-built deterministic SQL accounting plans)
- SPRouter (Native Sepehryar Stored Procedures router & whitelist)
- ReflectionEngine (Self-Correction & Query Relaxation)
- AgentOrchestrator Rich Financial Synthesizer
"""
from app.agent.market_ontology import MarketOntologyParser, SemanticIntent
from app.agent.golden_patterns import GoldenPatternsEngine
from app.agent.sp_router import sp_router
from app.agent.reflection import reflection_engine
from app.agent.orchestrator import agent_orchestrator
from app.agent.schemas import UserIntent, SQLPlan


def test_market_ontology_parsing():
    """Verify semantic classification of Persian business queries."""
    # Banks
    intent1 = MarketOntologyParser.parse_query("مانده حساب بانک ملت چقدره؟")
    assert intent1.concept == "bank_balance"
    assert "ملت" in intent1.extracted_names

    intent_all_banks = MarketOntologyParser.parse_query("موجودی حساب بانک‌ها رو بده")
    assert intent_all_banks.concept == "bank_balance"

    # Debtors & Creditors
    intent2 = MarketOntologyParser.parse_query("بدهکارترین مشتریان کیا هستن؟")
    assert intent2.concept == "top_debtors"

    intent3 = MarketOntologyParser.parse_query("بستانکارترین اشخاص کیا هستن؟")
    assert intent3.concept == "top_creditors"

    # Specific Person
    intent4 = MarketOntologyParser.parse_query("گردش حساب علی فکوری")
    assert intent4.concept == "specific_person_balance"
    assert any("فکوری" in name for name in intent4.extracted_names)

    # Cheques
    intent5 = MarketOntologyParser.parse_query("چک‌های برگشتی رو نشون بده")
    assert intent5.concept == "cheques_received"
    assert intent5.sub_concept == "bargashti"

    # Out of stock
    intent6 = MarketOntologyParser.parse_query("کالاهایی که موجودی ندارن")
    assert intent6.concept == "inventory_stock"
    assert intent6.sub_concept == "out_of_stock"


def test_golden_patterns_generation():
    """Verify golden SQL templates produce valid read-only SELECT queries."""
    # Bank balances
    plan_bank = GoldenPatternsEngine.generate_plan(
        SemanticIntent(concept="bank_balance", sub_concept="all_banks"),
        "مانده حساب بانک‌ها"
    )
    assert plan_bank is not None
    assert "Master" in plan_bank.target_tables
    assert "Srfsl = 100" in plan_bank.generated_sql
    assert "WITH (NOLOCK)" in plan_bank.generated_sql

    # Top Debtors
    plan_debt = GoldenPatternsEngine.generate_plan(
        SemanticIntent(concept="top_debtors"),
        "بدهکارترین مشتریان"
    )
    assert plan_debt is not None
    assert "Srfsl = 110" in plan_debt.generated_sql
    assert "[مانده بدهی به ما] DESC" in plan_debt.generated_sql

    # Top Creditors
    plan_cred = GoldenPatternsEngine.generate_plan(
        SemanticIntent(concept="top_creditors"),
        "بستانکارترین اشخاص"
    )
    assert plan_cred is not None
    assert "201" in plan_cred.generated_sql

    # Opening Voucher
    plan_open = GoldenPatternsEngine.generate_plan(
        SemanticIntent(concept="trial_balance_or_opening"),
        "سند افتتاحیه"
    )
    assert plan_open is not None
    assert "SanadM = 1" in plan_open.generated_sql


def test_sp_router():
    """Verify native stored procedure matching and plan creation."""
    matched = sp_router.match_procedure("کالاهای با موجودی منفی رو بیار")
    assert matched is not None
    assert matched.name == "_ssp_ListManfiKala"

    sp_plan = sp_router.build_plan(matched)
    assert sp_plan.generated_sql == "EXEC dbo._ssp_ListManfiKala"
    assert sp_plan.validation_status is True


def test_reflection_filter_relaxation():
    """Verify search filter relaxation when 0 rows match exact name."""
    sql = "SELECT * FROM TR WHERE p.Name LIKE N'%آقای علی فکوری%'"
    relaxed = reflection_engine._relax_search_filter(sql)
    assert "فکوری" in relaxed
    assert "آقای" not in relaxed


def test_orchestrator_financial_table_formatting():
    """Verify orchestrator formats financial rows into clean Markdown table with totals."""
    mock_plan = SQLPlan(
        goal="استخراج مانده حساب بانک‌ها",
        target_tables=["Master"],
        target_columns=["کد حساب", "عنوان حساب", "مانده نهایی"],
        generated_sql="SELECT 1",
        validation_status=True
    )
    mock_result = {
        "columns": ["کد حساب", "عنوان حساب", "مانده نهایی"],
        "rows": [
            {"کد حساب": 1626, "عنوان حساب": "صادرات منشادی", "مانده نهایی": 70000000000},
            {"کد حساب": 1627, "عنوان حساب": "صادرات عباسی", "مانده نهایی": 30000000000},
        ],
        "total_rows": 2
    }

    formatted = agent_orchestrator._format_data_response(
        query="مانده بانک‌ها",
        plan=mock_plan,
        result=mock_result
    )

    assert "صادرات منشادی" in formatted
    assert "70,000,000,000" in formatted
    assert "مجموع مانده نهایی:" in formatted
    assert "100,000,000,000" in formatted
    assert "بیشترین مقدار:" in formatted
