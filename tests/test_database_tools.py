"""
Tests for deterministic database tools and tool registry invocation.
"""
from app.tools.registry import tool_registry
import app.tools.database_tools as db_tools


def test_tool_registry_registration():
    """Verify core database tools are registered with Pydantic schemas."""
    tools = tool_registry.list_tools()
    tool_names = [t.name for t in tools]
    assert "inspect_database" in tool_names
    assert "inspect_table" in tool_names
    assert "inspect_column" in tool_names
    assert "find_relationships" in tool_names
    assert "get_table_row_count" in tool_names
    assert "get_sample_rows" in tool_names
    assert "validate_sql" in tool_names
    assert "run_safe_select" in tool_names


def test_inspect_database_tool():
    """Verify inspect_database returns summary counts."""
    res = db_tools.inspect_database(database_name="DEMO")
    assert res.total_tables >= 4
    assert res.total_views >= 1


def test_inspect_table_tool():
    """Verify inspect_table returns column attributes."""
    res = db_tools.inspect_table(table_name="TblKala", database_name="DEMO")
    assert res.table_name == "TblKala"
    assert res.columns_count >= 5
    assert "IDKala" in res.primary_keys


def test_get_table_row_count_tool():
    """Verify get_table_row_count tool returns row count."""
    res = db_tools.get_table_row_count(table_name="TblKala", database_name="DEMO")
    assert res.table_name == "TblKala"
    assert res.row_count > 0


def test_get_sample_rows_tool():
    """Verify get_sample_rows tool returns masked rows."""
    res = db_tools.get_sample_rows(table_name="TblPerson", limit=5, database_name="DEMO")
    assert res.table_name == "TblPerson"
    assert len(res.rows) > 0
    # Verify sensitive data masking applied
    first_row = res.rows[0]
    if "Mobile" in first_row and first_row["Mobile"]:
        assert "****" in str(first_row["Mobile"])
