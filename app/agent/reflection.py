"""
Self-Correction & Reflection Engine:
Validates SQL queries against real database execution, auto-corrects column/table mismatches,
and applies semantic relaxation if zero results are returned.
"""
import re
import time
from typing import Optional, Any
from app.agent.schemas import SQLPlan
from app.core.logger import get_logger
from app.database.safe_sql import safe_sql_executor

logger = get_logger("agent.reflection")


class ReflectionEngine:
    """Executes SQL with automatic error recovery and zero-result relaxation."""

    @classmethod
    def execute_with_reflection(
        cls,
        sql_plan: SQLPlan,
        database_name: Optional[str] = None,
        max_rows: int = 25
    ) -> tuple[dict[str, Any], list[str]]:
        """
        Executes query, catches SQL errors or zero rows, and iteratively refines.
        Returns: (result_dict, list_of_reflection_notes)
        """
        reflection_notes: list[str] = []
        current_sql = sql_plan.generated_sql

        # First Execution Attempt
        try:
            t0 = time.perf_counter()
            res = safe_sql_executor.execute_readonly_query(
                sql=current_sql,
                database=database_name,
                max_rows=max_rows,
                mask_sensitive=True
            )
            res_rows = res.get("total_rows", 0)

            # Check if 0 rows returned on a name-based search
            if res_rows == 0 and "LIKE N'%" in current_sql:
                # Reflection Step: Try broader token search
                logger.info("0 rows returned for exact match. Applying reflection relaxation...")
                relaxed_sql = cls._relax_search_filter(current_sql)
                if relaxed_sql != current_sql:
                    reflection_notes.append("جستجوی اولیه نتیجه‌ای نداشت؛ کوئری به جستجوی گسترده‌تر و کلمات کلیدی ریشه تغییر یافت.")
                    res_relaxed = safe_sql_executor.execute_readonly_query(
                        sql=relaxed_sql,
                        database=database_name,
                        max_rows=max_rows,
                        mask_sensitive=True
                    )
                    if res_relaxed.get("total_rows", 0) > 0:
                        sql_plan.generated_sql = relaxed_sql
                        return res_relaxed, reflection_notes

            return res, reflection_notes

        except Exception as sql_err:
            err_msg = str(sql_err)
            logger.warning(f"SQL execution failed in first pass: {err_msg}. Triggering self-correction...")
            reflection_notes.append(f"خطای ساختار پایگاه داده شناسایی شد: {err_msg[:60]}... (در حال اصلاح خودکار)")

            # Self-Correction: Fix invalid column names
            col_matches = re.findall(r"Invalid column name '([^']+)'", err_msg)
            if col_matches:
                fixed_sql = current_sql
                for bad_col in set(col_matches):
                    fixed_sql = cls._correct_bad_column(fixed_sql, bad_col)
                    reflection_notes.append(f"ستون نامعتبر '{bad_col}' از کوئری حذف یا اصلاح شد.")
                if fixed_sql != current_sql:
                    try:
                        res_fixed = safe_sql_executor.execute_readonly_query(
                            sql=fixed_sql,
                            database=database_name,
                            max_rows=max_rows,
                            mask_sensitive=True
                        )
                        sql_plan.generated_sql = fixed_sql
                        return res_fixed, reflection_notes
                    except Exception as e2:
                        logger.error(f"Second correction attempt failed: {e2}")

            # Fallback result on unrecoverable error
            return {
                "columns": [],
                "rows": [],
                "total_rows": 0,
                "duration_ms": 0.0,
                "error": err_msg
            }, reflection_notes

    @classmethod
    def _relax_search_filter(cls, sql: str) -> str:
        """Relax search filter by stripping common Persian prefixes from LIKE clauses."""
        # Replace multi-word LIKE N'%علی فکوری%' with single distinctive token N'%فکوری%'
        def clean_like_match(m):
            term = m.group(1).strip()
            tokens = [t for t in term.split() if len(t) > 2 and t not in ("آقای", "خانم", "شرکت", "فروشگاه")]
            if tokens:
                return f"LIKE N'%{tokens[-1]}%'"
            return m.group(0)

        relaxed = re.sub(r"LIKE\s+N'%([^%']+)%'", clean_like_match, sql)
        return relaxed

    @classmethod
    def _correct_bad_column(cls, sql: str, bad_column: str) -> str:
        """Remove or replace an invalid column name from SELECT statement."""
        # Remove bad column from SELECT list
        pattern = rf"\b{bad_column}\b(?:\s+AS\s+\[[^\]]+\])?(?:\s*,)?"
        fixed = re.sub(pattern, "", sql)
        # Clean trailing commas before FROM
        fixed = re.sub(r",\s+FROM\b", " FROM", fixed, flags=re.IGNORECASE)
        return fixed


reflection_engine = ReflectionEngine()
