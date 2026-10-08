"""
Tests for QueryBuilder and structured SQL plan generation.
"""
from app.database.query_builder import query_builder


def test_sanitize_identifier():
    """Verify identifier sanitization and bracket quoting."""
    assert query_builder.sanitize_identifier("TblKala") == "[TblKala]"
    assert query_builder.sanitize_identifier("[TblPerson]") == "[TblPerson]"
    assert query_builder.sanitize_identifier("dbo.TblKala") == "[dbo].[TblKala]"


def test_build_select_plan():
    """Verify query builder constructs valid SQLPlan with TOP clause."""
    plan = query_builder.build_select_plan(
        goal="استخراج لیست کالاها",
        table="TblKala",
        columns=["IDKala", "NameKala", "Mogodi"],
        where_clauses=["Mogodi > 0"],
        order_by="Mogodi DESC",
        top_limit=25
    )
    assert plan.validation_status is True
    assert "SELECT TOP (25) IDKala, NameKala, Mogodi FROM [TblKala]" in plan.generated_sql
    assert "WHERE Mogodi > 0" in plan.generated_sql
    assert "ORDER BY Mogodi DESC" in plan.generated_sql
    assert plan.row_limit == 25
    assert plan.is_readonly is True
