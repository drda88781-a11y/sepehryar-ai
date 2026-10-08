"""
Safe SQL Query Builder for SQL Server.
Constructs deterministic SELECT statements with automatic TOP clauses,
safe identifiers quoting, join resolution, and safety validation.
"""
from typing import Optional, Any
from app.agent.schemas import SQLPlan, RiskLevel
from app.database.safe_sql import SafeSQLValidator


class QueryBuilder:
    """Constructs safe, well-formed SQL Server SELECT queries."""

    @classmethod
    def sanitize_identifier(cls, name: str) -> str:
        """Strip dangerous characters and ensure safe bracket quoting."""
        clean = name.strip().replace(";", "").replace("--", "").replace("/*", "")
        if clean.startswith("[") and clean.endswith("]"):
            return clean
        # If it contains alias (e.g. TblKala.NameKala or COUNT(*) as cnt)
        if "." in clean:
            parts = clean.split(".")
            return ".".join(f"[{p.strip('[]')}]" for p in parts)
        if " " in clean or "(" in clean:
            # Expressions like COUNT(*) AS Total
            return clean
        return f"[{clean}]"

    @classmethod
    def build_select_plan(
        cls,
        goal: str,
        table: str,
        columns: Optional[list[str]] = None,
        where_clauses: Optional[list[str]] = None,
        joins: Optional[list[str]] = None,
        order_by: Optional[str] = None,
        top_limit: int = 100,
    ) -> SQLPlan:
        """
        Assemble a validated SQLPlan from structured parameters.
        Ensures TOP clause is enforced and read-only safety is verified.
        """
        cols_str = ", ".join(columns) if columns else "*"
        clean_table = cls.sanitize_identifier(table)

        sql_parts = [f"SELECT TOP ({top_limit}) {cols_str} FROM {clean_table}"]

        # Add JOINs
        if joins:
            for j in joins:
                sql_parts.append(j.strip())

        # Add WHERE
        if where_clauses:
            clean_wheres = [w.strip() for w in where_clauses if w.strip()]
            if clean_wheres:
                sql_parts.append("WHERE " + " AND ".join(clean_wheres))

        # Add ORDER BY
        if order_by:
            sql_parts.append(f"ORDER BY {order_by.strip()}")

        final_sql = " ".join(sql_parts)

        # Validate with SafeSQLValidator
        is_safe, reason = SafeSQLValidator.validate_query(final_sql)

        return SQLPlan(
            goal=goal,
            target_tables=[table],
            target_columns=columns or ["*"],
            where_filters=where_clauses or [],
            joins=joins or [],
            order_by=order_by,
            row_limit=top_limit,
            generated_sql=final_sql,
            is_readonly=True,
            risk_level=RiskLevel.LOW if is_safe else RiskLevel.HIGH,
            validation_status=is_safe,
            validation_message=reason or "کوئری ایمن و مجاز است."
        )


query_builder = QueryBuilder()
