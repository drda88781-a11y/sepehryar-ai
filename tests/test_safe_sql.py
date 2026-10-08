"""
Tests for SafeSQLValidator and SafeSQLExecutor ensuring complete blocking of destructive queries.
"""
import pytest
from app.core.exceptions import SafeSQLViolationError
from app.database.safe_sql import SafeSQLValidator, safe_sql_executor


def test_valid_select_allowed():
    """Verify safe SELECT and WITH queries pass validation."""
    valid_queries = [
        "SELECT * FROM TblKala",
        "SELECT TOP 10 IDKala, NameKala FROM TblKala WHERE Mogodi > 0",
        "WITH KalaCTE AS (SELECT IDKala FROM TblKala) SELECT * FROM KalaCTE",
    ]
    for q in valid_queries:
        is_safe, reason = SafeSQLValidator.validate_query(q)
        assert is_safe is True, f"Expected safe for query: {q}, reason: {reason}"


def test_block_insert():
    """Verify INSERT statements are strictly blocked."""
    sql = "INSERT INTO TblKala (NameKala) VALUES ('کالای تستی')"
    is_safe, reason = SafeSQLValidator.validate_query(sql)
    assert is_safe is False
    with pytest.raises(SafeSQLViolationError):
        safe_sql_executor.execute_readonly_query(sql, server="DEMO", database="DEMO")


def test_block_update():
    """Verify UPDATE statements are strictly blocked."""
    sql = "UPDATE TblKala SET Mogodi = 100 WHERE IDKala = 1"
    is_safe, reason = SafeSQLValidator.validate_query(sql)
    assert is_safe is False
    with pytest.raises(SafeSQLViolationError):
        safe_sql_executor.execute_readonly_query(sql, server="DEMO", database="DEMO")


def test_block_delete():
    """Verify DELETE statements are strictly blocked."""
    sql = "DELETE FROM TblKala WHERE IDKala = 1"
    is_safe, reason = SafeSQLValidator.validate_query(sql)
    assert is_safe is False
    with pytest.raises(SafeSQLViolationError):
        safe_sql_executor.execute_readonly_query(sql, server="DEMO", database="DEMO")


def test_block_drop_alter_truncate():
    """Verify administrative and DDL statements are blocked."""
    queries = [
        "DROP TABLE TblKala",
        "ALTER TABLE TblKala ADD TestCol INT",
        "TRUNCATE TABLE TblPerson",
        "EXEC sp_msforeachtable 'DROP TABLE ?'",
    ]
    for q in queries:
        is_safe, _ = SafeSQLValidator.validate_query(q)
        assert is_safe is False, f"Expected forbidden for: {q}"


def test_block_multiple_statements_semicolon_injection():
    """Verify semicolon multiple statement chaining is detected and rejected."""
    injections = [
        "SELECT * FROM TblKala; DROP TABLE TblPerson;",
        "SELECT TOP 5 * FROM TblKala; DELETE FROM TR;",
    ]
    for q in injections:
        is_safe, _ = SafeSQLValidator.validate_query(q)
        assert is_safe is False, f"Expected injection blocked for: {q}"
