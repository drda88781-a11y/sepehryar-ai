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
        q_lower = query.lower().strip()

        # Greetings & conversational pleasantries (Immediate response, zero DB)
        greetings = ["سلام", "درود", "صبح بخیر", "عصر بخیر", "شب بخیر", "خسته نباشید", "خسته نباشی", "روز بخیر", "چطوری", "خوبی", "سلام علیکم", "hi", "hello"]
        clean_words = q_lower.split()
        if any(q_lower == g or q_lower.startswith(g + " ") or q_lower.startswith(g + "!") or q_lower.startswith(g + "،") for g in greetings) and len(clean_words) <= 5:
            return IntentDetectionResult(
                intent=UserIntent.GENERAL_ACCOUNTING,
                confidence=0.99,
                requires_database=False,
                requires_knowledge=False,
                requires_tools=[],
                summary_reasoning="پیام احوال‌پرسی یا آغاز مکالمه است."
            )

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

        # Accounting & SQL Programming Copilot inquiries (Full Mastery, Zero Local DB needed)
        accounting_and_sql_keywords = [
            "چطور", "چگونه", "چطوری", "چجوری", "نحوه", "الگو", "الگوی", "راهکار", "روش", "طریقه", "دستورالعمل", "مراحل",
            "ثبت کنم", "ثبت بکنم", "درج کنم", "درج بکنم", "تعریف کنم", "تعریف بکنم", "تعریف کردن", "تعریف",
            "کدینگ", "سرفصل چیست", "معین چیست", "تفصیلی چیست", "مهاجرت داده", "چیکار کنم", "چه کار کنم",
            "توضیح بده", "راهنما", "آموزش", "یاد بده", "اسکریپت", "تریگر", "قوانین", "معماری",
            "چیست", "چیه", "کاربرد", "کاربردی دارد", "معرفی", "فرمول", "مفهوم", "تفاوت", "مقایسه",
            "اصول حسابداری", "استاندارد", "استانداردهای حسابداری", "ثبت سند", "ثبت دوبل", "سند افتتاحیه", "سند اختتامیه",
            "ترازنامه", "سود و زیان", "استهلاک", "بهای تمام شده", "ارزش افزوده", "مالیات", "ماهیت حساب",
            "مبنای تعهدی", "مبنای نقدی", "نسبت جاری", "نسبت آنی", "سرمایه در گردش", "fifo", "lifo", "میانگین موزون",
            "کوئری بنویس", "کد بنویس", "دستور بنویس", "sql بنویس", "کوئری sql", "کدهای sql", "دستورات sql",
            "window function", "row_number", "dense_rank", "partition by", "cte", "recursive", "join چیست", "اینمپ",
            "ایندکس", "پرفورمنس", "بهینه‌سازی", "deadlock", "transaction", "stored procedure", "view", "function"
        ]
        is_expert_reasoning = any(w in q_lower for w in accounting_and_sql_keywords)

        # Phrases asking for explanation, tutorial, or code writing (NOT company data fetch)
        is_instructional = any(w in q_lower for w in [
            "توضیح بده", "یاد بده", "مثال بزن", "مثال بده", "کوئری بنویس", "کد بنویس", "اسکریپت بنویس",
            "اسکریپت بده", "کد بده", "کوئری بده", "دستور بده", "راهکار بده", "اسکریپت", "اسکریپتش",
            "چطوری بنویسم", "چگونه بنویسم", "چطور ثبت", "نحوه ثبت", "سندش چیه", "ثبتش چیه", "فرمولش چیه",
            "پاک کنم", "حذف کنم", "چطور پاک کنم", "چگونه پاک کنم", "چطور حذف کنم", "چگونه حذف کنم",
            "تفاوت", "فرق", "مقایسه", "چیست", "چیه"
        ])

        # Explicit data fetch commands for company's local database
        data_fetch_verbs = ["بیار", "بده", "نشون بده", "نمایش بده", "استخراج کن", "لیست", "چقدره", "چقدر است", "چند تاست"]
        is_explicit_fetch = any(w in q_lower for w in data_fetch_verbs) and not is_instructional

        # Check if user specifically asks to fetch/show company financial records
        is_retrieval = is_explicit_fetch and not is_expert_reasoning

        # If it's a general accounting, financial principles, or SQL programming question
        if is_expert_reasoning or is_instructional:
            return IntentDetectionResult(
                intent=UserIntent.GENERAL_ACCOUNTING,
                confidence=0.96,
                requires_database=False,
                requires_knowledge=True,
                requires_tools=["search_knowledge_base"],
                summary_reasoning="کاربر پرسشی درباره اصول حسابداری، استانداردهای مالی یا برنامه‌نویسی و کوئری‌های SQL دارد."
            )

        # Database Query (Data retrieval from local company database)
        entities = []
        if any(w in q_lower for w in ["کالا", "موجودی", "قیمت", "اجناس", "بارکد"]):
            entities.append("TblKala")
        if any(w in q_lower for w in ["مشتری", "فروشنده", "طرف حساب", "شخص", "اشخاص", "بدهکار", "بستانکار", "بانک"]):
            entities.append("TblPerson")
        if any(w in q_lower for w in ["فاکتور", "فروش", "خرید", "تراکنش", "ریز"]):
            entities.append("TR")
        if any(w in q_lower for w in ["سند", "حسابداری", "آرتیکل"]):
            entities.append("TblSanad")

        if not is_retrieval and not entities:
            return IntentDetectionResult(
                intent=UserIntent.GENERAL_ACCOUNTING,
                confidence=0.85,
                requires_database=False,
                requires_knowledge=True,
                requires_tools=["search_knowledge_base"],
                summary_reasoning="پرسش عمومی یا مفهومی بدون قصد استخراج داده‌های جدول."
            )

        return IntentDetectionResult(
            intent=UserIntent.DATABASE_QUERY,
            confidence=0.88,
            requires_database=True,
            requires_knowledge=False,
            requires_tools=["run_safe_select"],
            extracted_entities=entities,
            summary_reasoning="کاربر درخواست استخراج یا آمار داده‌های مالی و حسابداری از دیتابیس لوکال را دارد."
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
        # 1. Native Stored Procedures Discovery & Execution
        from app.agent.sp_router import sp_router
        matched_sp = sp_router.match_procedure(query)
        if matched_sp:
            return sp_router.build_plan(matched_sp)

        # 2. Semantic Market Parsing & Golden Accounting Patterns
        from app.agent.market_ontology import MarketOntologyParser
        from app.agent.golden_patterns import GoldenPatternsEngine

        semantic_intent = MarketOntologyParser.parse_query(query)
        golden_plan = GoldenPatternsEngine.generate_plan(semantic_intent, query, active_schema=active_schema)
        if golden_plan:
            return golden_plan

        q_lower = query.lower()

        # 2. Total Products Count
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
                ["Name", "NameKala"],
                ["Mande", "Mogodi"],
                ["Bprice", "GhimatForosh", "FiKharid"],
                ["CodeKala", "BaghaliCode"],
            ], active_schema)
            inv_col = "Mande" if "Mande" in cols else ("Mogodi" if "Mogodi" in cols else None)
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
                ["Sh_ozviat", "IDPerson", "Code"],
                ["Name"],
                ["Famil", "Family"],
                ["Mobile"],
                ["Tell", "Tel"],
                ["Etebar", "RemainAccount"],
            ], active_schema)
            bal_col = "Etebar" if "Etebar" in cols else ("RemainAccount" if "RemainAccount" in cols else None)
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
                ["Sh_ozviat", "IDPerson", "Code"],
                ["Name"],
                ["Famil", "Family"],
                ["Type"],
                ["Mobile"],
                ["Tell", "Tel"],
                ["Etebar", "RemainAccount"],
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

        # No specific SQL pattern matched - return None to allow cognitive/knowledge reasoning fallback
        return None


task_planner = TaskPlanner()
