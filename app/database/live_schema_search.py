"""
Live Schema & Dynamic Column Searcher for SQL Server.
Searches INFORMATION_SCHEMA.COLUMNS, sys.tables, and live reporting configurations
dynamically so the agent never gives rote or memorized fallback answers.
"""
from typing import Optional, Any
from app.database.connection import db_connection_manager
from app.database.report_inspector import report_inspector


class LiveSchemaSearcher:
    """Dynamically resolves tables, views, and columns from the live SQL Server database."""

    @classmethod
    def search_columns(cls, query: str, limit: int = 25) -> list[dict[str, str]]:
        """Search columns in the active SQL Server database matching keywords."""
        q_clean = query.lower().replace("ي", "ی").replace("ك", "ک")
        # Extract potential English words or transliterated keywords
        keywords = []
        for word in q_clean.split():
            if len(word) >= 2 and word not in ["ستون", "ستونهای", "ستون‌های", "فیلد", "فیلدهای", "جدول", "چیه", "چیست", "در", "از", "رو"]:
                keywords.append(word)

        if not keywords:
            return []

        conditions = []
        params = []
        for kw in keywords[:3]:
            conditions.append("(COLUMN_NAME LIKE ? OR TABLE_NAME LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%"])

        where_clause = " OR ".join(conditions)
        sql = f"""
        SELECT TOP ({limit}) TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE {where_clause}
        ORDER BY TABLE_NAME, ORDINAL_POSITION;
        """

        results = []
        try:
            with db_connection_manager.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, params)
                for row in cur.fetchall():
                    results.append({
                        "table": row[0],
                        "column": row[1],
                        "type": row[2],
                        "nullable": row[3]
                    })
        except Exception:
            pass

        return results

    @classmethod
    def answer_column_or_report_query(cls, query: str) -> Optional[str]:
        """Synthesize live database facts for columns and report queries."""
        q_norm = query.lower()

        # 1. Check Report Inspector (Stimulsoft MRT files) if report/invoice/print is mentioned
        is_report_query = any(w in q_norm for w in ["گزارش", "چاپ", "پرینت", "قالب", "فاکتور", "حواله", "a4", "a5", "استیمول", "mrt", "طراحی"])
        mrt_explanation = None
        if is_report_query:
            mrt_explanation = report_inspector.explain_report_structure(query)

        # 2. Check live SQL Server columns
        cols = cls.search_columns(query)

        if not mrt_explanation and not cols:
            return None

        lines = []
        if mrt_explanation:
            lines.append(mrt_explanation)
            lines.append("\n---\n")

        if cols:
            lines.append("### 🔍 ستون‌ها و فیلدهای منطبق در دیتابیس زنده SQL Server:")
            # Group by table
            by_table = {}
            for c in cols:
                by_table.setdefault(c["table"], []).append(f"`{c['column']}` ({c['type']})")

            for tbl, clist in list(by_table.items())[:6]:
                lines.append(f"• **جدول `{tbl}`:** {', '.join(clist[:10])}")
                if len(clist) > 10:
                    lines.append(f"  *(و {len(clist) - 10} ستون دیگر)*")

        return "\n".join(lines)


live_schema_searcher = LiveSchemaSearcher()
