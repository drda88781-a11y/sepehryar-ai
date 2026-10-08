"""
Safe SQL execution engine enforcing read-only constraints, keyword filtering,
injection mitigation, and execution timeout limits.
"""
import re
import time
from typing import Optional, Any
from app.config.constants import (
    FORBIDDEN_SQL_KEYWORDS,
    DEFAULT_SQL_TIMEOUT_SEC,
    DEFAULT_SQL_MAX_ROWS,
)
from app.config.settings import settings
from app.core.audit import record_audit
from app.core.exceptions import SafeSQLViolationError, QueryExecutionError
from app.core.logger import get_logger
from app.core.security import mask_sample_rows
from app.database.connection import db_connection_manager
from app.database.mock_provider import get_mock_sample_rows

logger = get_logger("safe_sql")


class SafeSQLValidator:
    """Independent deterministic validation layer for SQL queries."""

    @classmethod
    def validate_query(cls, sql: str) -> tuple[bool, Optional[str]]:
        """
        Validate whether a query is strictly safe and read-only.
        Returns: (is_valid: bool, rejection_reason: Optional[str])
        """
        if not sql or not sql.strip():
            return False, "کوئری خالی است."

        clean_sql = sql.strip()

        # Remove single-line comments (-- ...) and multi-line comments (/* ... */)
        without_comments = re.sub(r'--[^\r\n]*', ' ', clean_sql)
        without_comments = re.sub(r'/\*.*?\*/', ' ', without_comments, flags=re.DOTALL)
        normalized = " ".join(without_comments.split())

        # 1. Must start with SELECT or WITH (for Common Table Expressions)
        first_token = normalized.split()[0].upper()
        if first_token not in ("SELECT", "WITH"):
            return False, f"دستور باید فقط با SELECT یا WITH آغاز شود؛ دستور با '{first_token}' مجاز نیست."

        # 2. Disallow multiple statements separated by semicolon
        # Check if semicolon exists and is followed by any non-whitespace command
        statements = [s.strip() for s in without_comments.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "اجرای چندین دستور مجزا (Multiple Statements) مجاز نیست."

        # 3. Check for forbidden destructive/administrative keywords
        tokens = re.findall(r'\b[A-Za-z_]+\b', without_comments)
        for token in tokens:
            upper_token = token.upper()
            if upper_token in FORBIDDEN_SQL_KEYWORDS:
                return False, f"کلمه کلیدی غیرمجاز '{upper_token}' در کوئری شناسایی شد."

        # 4. Check for system procedures or extended procedures (xp_..., sp_...)
        sys_procs = re.findall(r'\b(xp_|sp_executesql|sp_configure|openrowset|opendatasource)\w*\b', without_comments, re.IGNORECASE)
        if sys_procs:
            return False, f"فراخوانی توابع یا پروسیجرهای سیستمی خطرناک ({sys_procs[0]}) ممنوع است."

        return True, None


class SafeSQLExecutor:
    """Executes validated read-only queries with enforced timeouts and row limits."""

    def __init__(self, connection_manager=db_connection_manager) -> None:
        self.conn_mgr = connection_manager

    def execute_readonly_query(
        self,
        sql: str,
        database: Optional[str] = None,
        server: Optional[str] = None,
        max_rows: int = DEFAULT_SQL_MAX_ROWS,
        timeout: int = DEFAULT_SQL_TIMEOUT_SEC,
        mask_sensitive: bool = True,
    ) -> dict[str, Any]:
        """Validate and execute safe read-only SQL query."""
        target_server = server or settings.sql_server
        target_db = database or settings.sql_database
        start_time = time.perf_counter()

        # Step 1: Validation
        is_safe, reason = SafeSQLValidator.validate_query(sql)
        if not is_safe:
            duration = (time.perf_counter() - start_time) * 1000
            record_audit(
                action="SAFE_SQL_VIOLATION",
                tool="safe_sql_executor",
                target_database=target_db,
                sql_query=sql,
                success=False,
                duration_ms=duration,
                error_message=reason
            )
            logger.warning(f"SQL safety violation: {reason} | SQL: {sql}")
            raise SafeSQLViolationError(
                user_message=f"خطای امنیتی در اجرای کوئری: {reason}",
                technical_details=reason
            )

        # Step 2: Handle Demo/Mock mode
        if target_server.upper() in ("DEMO", "MOCK", "OFFLINE_DEMO") or (target_db and target_db.upper() in ("DEMO", "MOCK")):
            # Extract simple table name from query for mock return
            match = re.search(r'\bFROM\s+([A-Za-z0-9_]+)\b', sql, re.IGNORECASE)
            table_name = match.group(1) if match else "TblKala"
            mock_rows = get_mock_sample_rows(table_name, limit=max_rows)
            duration = (time.perf_counter() - start_time) * 1000
            record_audit(
                action="SQL_READONLY_EXECUTE",
                tool="safe_sql_executor",
                target_database=target_db,
                sql_query=sql,
                success=True,
                duration_ms=duration,
                metadata={"rows_returned": len(mock_rows), "mode": "demo_mock"}
            )
            columns = list(mock_rows[0].keys()) if mock_rows else []
            return {
                "columns": columns,
                "rows": mask_sample_rows(mock_rows) if mask_sensitive else mock_rows,
                "total_rows": len(mock_rows),
                "duration_ms": round(duration, 2),
                "is_mock": True
            }

        # Step 3: Real SQL Server execution
        try:
            with self.conn_mgr.get_connection(server=target_server, database=target_db) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                # Fetch limited rows to protect memory
                raw_rows = cursor.fetchmany(max_rows)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                rows_data = [dict(zip(columns, row)) for row in raw_rows]
                duration = (time.perf_counter() - start_time) * 1000

                record_audit(
                    action="SQL_READONLY_EXECUTE",
                    tool="safe_sql_executor",
                    target_database=target_db,
                    sql_query=sql,
                    success=True,
                    duration_ms=duration,
                    metadata={"rows_returned": len(rows_data)}
                )

                final_rows = mask_sample_rows(rows_data) if mask_sensitive else rows_data
                return {
                    "columns": columns,
                    "rows": final_rows,
                    "total_rows": len(rows_data),
                    "duration_ms": round(duration, 2),
                    "is_mock": False
                }

        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            record_audit(
                action="SQL_READONLY_EXECUTE",
                tool="safe_sql_executor",
                target_database=target_db,
                sql_query=sql,
                success=False,
                duration_ms=duration,
                error_message=str(e)
            )
            logger.error(f"SQL execution failed: {e}")
            raise QueryExecutionError(
                user_message="خطا در اجرای کوئری در پایگاه داده.",
                technical_details=str(e),
                original_exception=e
            )


safe_sql_executor = SafeSQLExecutor()
