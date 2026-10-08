"""
Planner and Intent Detection engine translating natural language queries
into structured operational plans and safe SQL execution strategies.
"""
import re
from typing import Optional, Any
from app.agent.schemas import (
    UserIntent,
    RiskLevel,
    IntentDetectionResult,
    SQLPlan,
)
from app.database.query_builder import query_builder
from app.database.safe_sql import SafeSQLValidator


class TaskPlanner:
    """Detects user intent and formulates deterministic execution plans."""

    @classmethod
    def detect_intent(cls, query: str) -> IntentDetectionResult:
        """Classify user's query into predefined categories and identify candidate entities."""
        q_lower = query.lower()

        # Troubleshooting / Diagnostics
        if any(w in q_lower for w in ["خطا", "وصل نمیشه", "ارور", "سرویس", "قطع", "استاپ", "stop"]):
            return IntentDetectionResult(
                intent=UserIntent.TROUBLESHOOTING,
                confidence=0.95,
                requires_database=False,
                requires_knowledge=True,
                requires_tools=["check_sql_service", "check_database_connection"],
                summary_reasoning="کاربر گزارش خطا یا مشکل در اتصال داده است."
            )

        # System Health
        if any(w in q_lower for w in ["سلامت سیستم", "وضعیت سرور", "حافظه", "رم", "پردازنده", "دیسک", "cpu", "ram"]):
            return IntentDetectionResult(
                intent=UserIntent.SYSTEM_HEALTH,
                confidence=0.92,
                requires_database=False,
                requires_knowledge=False,
                requires_tools=["check_cpu_and_ram", "check_disk_space"],
                summary_reasoning="کاربر درخواست گزارش منابع سخت‌افزاری سرور را دارد."
            )

        # Schema Inspection & Relationships
        if any(w in q_lower for w in ["ارتباط", "کلید خارجی", "ستون", "ساختار جدول", "فیلد", "foreign key", "schema"]):
            entities = []
            if "tblkala" in q_lower or "کالا" in q_lower:
                entities.append("TblKala")
            if "tblperson" in q_lower or "شخص" in q_lower or "مشتری" in q_lower:
                entities.append("TblPerson")
            if "tr" in q_lower or "فاکتور" in q_lower:
                entities.append("TR")

            return IntentDetectionResult(
                intent=UserIntent.SCHEMA_INSPECTION,
                confidence=0.90,
                requires_database=True,
                requires_knowledge=False,
                requires_tools=["find_relationships", "inspect_table"],
                extracted_entities=entities,
                summary_reasoning="کاربر در حال بررسی متادیتا، ساختار و روابط پایگاه داده است."
            )

        # General Accounting / Knowledge / Coding questions
        if any(w in q_lower for w in ["کدینگ", "سرفصل", "معین", "حساب کل", "تفصیلی", "مهاجرت", "چگونه", "چطور", "توضیح", "راهنما", "آموزش", "مغایرت"]):
            return IntentDetectionResult(
                intent=UserIntent.GENERAL_ACCOUNTING,
                confidence=0.92,
                requires_database=False,
                requires_knowledge=True,
                requires_tools=["search_knowledge_base"],
                summary_reasoning="کاربر پرسشی درباره مفاهیم حسابداری، کدینگ سرفصل‌ها یا راهنماهای سیستمی دارد."
            )

        # Database Query (Data retrieval)
        entities = []
        if any(w in q_lower for w in ["کالا", "موجودی", "قیمت", "اجناس", "بارکد"]):
            entities.append("TblKala")
        if any(w in q_lower for w in ["مشتری", "فروشنده", "طرف حساب", "شخص", "اشخاص", "بدهکار", "بستانکار", "بانک"]):
            entities.append("TblPerson")
        if any(w in q_lower for w in ["فاکتور", "فروش", "خرید", "تراکنش", "ریز"]):
            entities.append("TR")
        if any(w in q_lower for w in ["سند", "حسابداری", "آرتیکل"]):
            entities.append("TblSanad")

        return IntentDetectionResult(
            intent=UserIntent.DATABASE_QUERY,
            confidence=0.88,
            requires_database=True,
            requires_knowledge=False,
            requires_tools=["run_safe_select"],
            extracted_entities=entities,
            summary_reasoning="کاربر درخواست استخراج یا آمار داده‌های مالی و حسابداری دارد."
        )

    @classmethod
    def _resolve_columns(cls, table_name: str, candidates: list[list[str]], schema: Optional[Any] = None) -> list[str]:
        """Resolve column names based on available columns in the active schema."""
        available = set()
        if schema:
            if isinstance(schema, dict) and "tables" in schema:
                tbl_info = schema["tables"].get(table_name, {})
                cols = tbl_info.get("columns", {})
                available = set(cols.keys()) if isinstance(cols, dict) else set(cols)
            elif hasattr(schema, "tables") and table_name in schema.tables:
                available = set(schema.tables[table_name].columns.keys())

        if not available:
            return [group[0] for group in candidates]

        resolved = []
        for group in candidates:
            for option in group:
                if option in available:
                    resolved.append(option)
                    break
        unique_resolved = list(dict.fromkeys(resolved))
        return unique_resolved if unique_resolved else list(available)[:6]

    @classmethod
    def generate_sql_plan(cls, query: str, active_schema: Optional[Any] = None) -> Optional[SQLPlan]:
        """Formulate a validated read-only SQL execution plan for the query."""
        q_lower = query.lower()

        # 1. Total Products Count
        if any(w in q_lower for w in ["تعداد کالا", "چند تا کالا", "تعداد کل کالاها", "کالاها چندتاست"]):
            return query_builder.build_select_plan(
                goal="محاسبه تعداد کل رکوردهای کالا",
                table="TblKala",
                columns=["COUNT(*) AS TotalCount"],
                top_limit=1
            )

        # 2. Inventory / Products List
        if any(w in q_lower for w in ["موجودی", "لیست کالاها", "کالاهای موجود"]):
            cols = cls._resolve_columns("TblKala", [
                ["IDKala"],
                ["CodeKala", "BaghaliCode"],
                ["NameKala", "Name"],
                ["Mogodi", "Mande"],
                ["GhimatForosh", "Bprice", "FiKharid"],
            ], active_schema)
            inv_col = "Mogodi" if "Mogodi" in cols else ("Mande" if "Mande" in cols else None)
            where = [f"{inv_col} > 0"] if inv_col else []
            order = f"{inv_col} DESC" if inv_col else None

            return query_builder.build_select_plan(
                goal="استخراج کالاهای موجود در انبار",
                table="TblKala",
                columns=cols,
                where_clauses=where,
                order_by=order,
                top_limit=20
            )

        # 3. Debtors (Customers / Persons)
        if any(w in q_lower for w in ["بدهکار", "بدهکارترین", "بیشترین بدهی"]):
            cols = cls._resolve_columns("TblPerson", [
                ["IDPerson", "Sh_ozviat"],
                ["Code", "Sh_ozviat"],
                ["Name"],
                ["Family", "Famil"],
                ["Mobile"],
                ["Tel", "Tell"],
                ["RemainAccount", "Etebar"],
            ], active_schema)
            bal_col = "RemainAccount" if "RemainAccount" in cols else ("Etebar" if "Etebar" in cols else None)
            where = [f"{bal_col} < 0"] if bal_col == "RemainAccount" else []
            order = f"{bal_col} ASC" if bal_col else None

            return query_builder.build_select_plan(
                goal="استخراج طرف‌حساب‌ها و بدهکاران",
                table="TblPerson",
                columns=cols,
                where_clauses=where,
                order_by=order,
                top_limit=10
            )

        # 4. Customers List
        if any(w in q_lower for w in ["مشتری", "لیست مشتریان", "اشخاص"]):
            cols = cls._resolve_columns("TblPerson", [
                ["IDPerson", "Sh_ozviat"],
                ["Code", "Sh_ozviat"],
                ["Name"],
                ["Family", "Famil"],
                ["Type"],
                ["Mobile"],
                ["RemainAccount", "Etebar"],
            ], active_schema)

            return query_builder.build_select_plan(
                goal="مشاهده فهرست اشخاص و طرف‌حساب‌ها",
                table="TblPerson",
                columns=cols,
                top_limit=20
            )

        # 5. Recent Sales / Invoices Transactions
        if any(w in q_lower for w in ["فروش", "فاکتور", "تراکنش"]):
            cols = cls._resolve_columns("TR", [
                ["IDTR"],
                ["IDKala"],
                ["IdPerson"],
                ["Tarikh", "Date"],
                ["Ted"],
                ["Fee"],
                ["Mab"],
                ["Sharh"],
            ], active_schema)

            return query_builder.build_select_plan(
                goal="استخراج جدیدترین تراکنش‌های فاکتور",
                table="TR",
                columns=cols,
                order_by="IDTR DESC" if "IDTR" in cols else None,
                top_limit=20
            )

        # Default fallback query for general inspection
        cols = cls._resolve_columns("TblKala", [
            ["IDKala"],
            ["NameKala", "Name"],
            ["GhimatForosh", "Bprice"],
            ["Mogodi", "Mande"],
        ], active_schema)
        return query_builder.build_select_plan(
            goal="نمایش نمونه داده‌های اولیه کالا",
            table="TblKala",
            columns=cols,
            top_limit=10
        )


task_planner = TaskPlanner()
