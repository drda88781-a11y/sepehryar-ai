"""
Golden Accounting Patterns for Sepehryar ERP:
Pre-built, deterministic, highly-optimized SQL query templates for core accounting operations.
"""
from typing import Optional, Any
from app.agent.market_ontology import SemanticIntent
from app.agent.schemas import SQLPlan


class GoldenPatternsEngine:
    """Produces verified, high-performance read-only SQL plans for Sepehryar accounting scenarios."""

    @classmethod
    def generate_plan(cls, intent: SemanticIntent, raw_query: str, active_schema: Optional[Any] = None) -> Optional[SQLPlan]:
        concept = intent.concept

        # 1. Bank & Cash Balances
        if concept == "bank_balance":
            bank_name = intent.extracted_names[0] if intent.extracted_names else None
            where_sql = "WHERE m.Srfsl = 100"
            if bank_name:
                if bank_name == "صندوق":
                    where_sql += " AND m.Moin = 1"
                else:
                    where_sql += f" AND (h.Text LIKE N'%{bank_name}%' OR m.Moin = 2)"
            else:
                where_sql += " AND m.Moin IN (1, 2)"

            sql = f"""
SELECT TOP (20)
    m.Srfsl,
    m.Moin,
    m.HSB AS [کد حساب],
    COALESCE(h.Text, p.Name, N'حساب ' + CAST(m.HSB AS NVARCHAR)) AS [عنوان حساب],
    m.Bed AS [گردش بدهکار],
    m.Bes AS [گردش بستانکار],
    (m.Bed - m.Bes) AS [مانده نهایی]
FROM dbo.Master m WITH (NOLOCK)
LEFT JOIN dbo.TblHesabText h WITH (NOLOCK) ON m.Srfsl = h.Srfsl AND m.Moin = h.Moin AND m.HSB = h.HSB
LEFT JOIN dbo.TblPerson p WITH (NOLOCK) ON m.personcod = p.Sh_ozviat
{where_sql}
ORDER BY [مانده نهایی] DESC
            """.strip()

            return SQLPlan(
                goal=f"استخراج مانده و گردش حساب‌های نقد و بانک ({bank_name or 'کلیه بانک‌ها'})",
                target_tables=["Master", "TblHesabText", "TblPerson"],
                target_columns=["HSB", "Text", "Bed", "Bes"],
                where_filters=[where_sql],
                generated_sql=sql,
                validation_status=True,
                row_limit=20
            )

        # 2. Specific Person Balance & Turnover
        if concept == "specific_person_balance":
            p_name = intent.extracted_names[0] if intent.extracted_names else ""
            p_code = intent.extracted_codes[0] if intent.extracted_codes else None

            where_cond = []
            if p_code:
                where_cond.append(f"(p.Sh_ozviat = {p_code} OR p.Hesab = {p_code} OR tr.HSB = {p_code})")
            if p_name:
                where_cond.append(f"(p.Name LIKE N'%{p_name}%' OR h.Text LIKE N'%{p_name}%' OR tr.Sharh LIKE N'%{p_name}%')")

            where_str = " AND ".join(where_cond) if where_cond else "1=1"

            sql = f"""
SELECT TOP (25)
    tr.DateR AS [تاریخ سند],
    tr.SanadM AS [شماره سند],
    tr.Sharh AS [شرح آرتیکل],
    COALESCE(p.Name, h.Text) AS [طرف حساب],
    p.Mobile AS [موبایل],
    tr.Bed AS [بدهکار],
    tr.Bes AS [بستانکار],
    (m.Bed - m.Bes) AS [مانده کل شخص]
FROM dbo.TR tr WITH (NOLOCK)
LEFT JOIN dbo.Master m WITH (NOLOCK) ON tr.Srfsl = m.Srfsl AND tr.Moin = m.Moin AND tr.HSB = m.HSB
LEFT JOIN dbo.TblPerson p WITH (NOLOCK) ON m.personcod = p.Sh_ozviat OR tr.Taraf = p.Sh_ozviat
LEFT JOIN dbo.TblHesabText h WITH (NOLOCK) ON tr.Srfsl = h.Srfsl AND tr.Moin = h.Moin AND tr.HSB = h.HSB
WHERE {where_str}
ORDER BY tr.SanadM DESC, tr.Sodor DESC
            """.strip()

            return SQLPlan(
                goal=f"استخراج گردش و صورت‌حساب شخص ({p_name or p_code})",
                target_tables=["TR", "TblPerson", "TblHesabText", "Master"],
                target_columns=["DateR", "SanadM", "Sharh", "Name", "Bed", "Bes"],
                where_filters=where_cond,
                generated_sql=sql,
                validation_status=True,
                row_limit=25
            )

        # 3. Top Debtors (بدهکارترین مشتریان)
        if concept == "top_debtors":
            sql = """
SELECT TOP (20)
    m.HSB AS [کد حساب],
    COALESCE(h.Text, p.Name, N'حساب ' + CAST(m.HSB AS NVARCHAR)) AS [نام طرف حساب],
    p.Mobile AS [موبایل],
    p.Tell AS [تلفن],
    m.Bed AS [کل بدهکاری],
    m.Bes AS [کل بستانکاری],
    (m.Bed - m.Bes) AS [مانده بدهی به ما]
FROM dbo.Master m WITH (NOLOCK)
LEFT JOIN dbo.TblHesabText h WITH (NOLOCK) ON m.Srfsl = h.Srfsl AND m.Moin = h.Moin AND m.HSB = h.HSB
LEFT JOIN dbo.TblPerson p WITH (NOLOCK) ON m.personcod = p.Sh_ozviat
WHERE m.Srfsl = 110 AND m.Moin = 1 AND (m.Bed - m.Bes) > 0
ORDER BY [مانده بدهی به ما] DESC
            """.strip()

            return SQLPlan(
                goal="استخراج لیست بدهکارترین مشتریان و مانده بدهی آنها",
                target_tables=["Master", "TblHesabText", "TblPerson"],
                target_columns=["HSB", "Name", "Mobile", "Bed", "Bes"],
                generated_sql=sql,
                validation_status=True,
                row_limit=20
            )

        # 4. Top Creditors (بستانکارترین تأمین‌کنندگان / اشخاص)
        if concept == "top_creditors":
            sql = """
SELECT TOP (20)
    m.HSB AS [کد حساب],
    COALESCE(h.Text, p.Name, N'حساب ' + CAST(m.HSB AS NVARCHAR)) AS [نام طرف حساب],
    p.Mobile AS [موبایل],
    m.Bes AS [کل بستانکاری],
    m.Bed AS [کل پرداختی],
    (m.Bes - m.Bed) AS [مانده طلب از ما]
FROM dbo.Master m WITH (NOLOCK)
LEFT JOIN dbo.TblHesabText h WITH (NOLOCK) ON m.Srfsl = h.Srfsl AND m.Moin = h.Moin AND m.HSB = h.HSB
LEFT JOIN dbo.TblPerson p WITH (NOLOCK) ON m.personcod = p.Sh_ozviat
WHERE (m.Srfsl = 201 OR (m.Srfsl = 110 AND m.Moin = 1)) AND (m.Bes - m.Bed) > 0
ORDER BY [مانده طلب از ما] DESC
            """.strip()

            return SQLPlan(
                goal="استخراج لیست بستانکاران و تأمین‌کنندگان تجاری",
                target_tables=["Master", "TblHesabText", "TblPerson"],
                target_columns=["HSB", "Name", "Mobile", "Bes", "Bed"],
                generated_sql=sql,
                validation_status=True,
                row_limit=20
            )

        # 5. Cheques Status (دریافتی یا پرداختی)
        if concept in ("cheques_received", "cheques_paid"):
            is_recv = (concept == "cheques_received")
            tbl = "[Check]" if is_recv else "CheckPardakht"
            sub = intent.sub_concept or "all"

            where_clauses = []
            if sub == "bargashti":
                where_clauses.append("State = 2")
            elif sub == "passed":
                where_clauses.append("State = 1")
            elif sub == "in_hand":
                where_clauses.append("State = 0")
            elif sub == "in_collection":
                where_clauses.append("State = 3")

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            sql = f"""
SELECT TOP (25)
    Id AS [شناسه چک],
    serial AS [شماره چک],
    mab AS [مبلغ چک (ریال)],
    DateChek AS [تاریخ سررسید],
    DateR AS [تاریخ ثبت],
    Bank AS [بانک],
    sharh AS [شرح / صاحب چک],
    CASE State
        WHEN 0 THEN N'نزد صندوق'
        WHEN 1 THEN N'پاس / وصول شده'
        WHEN 2 THEN N'برگشتی / واخواست'
        WHEN 3 THEN N'در جریان وصول بانکی'
        ELSE N'سایر'
    END AS [وضعیت]
FROM dbo.{tbl} WITH (NOLOCK)
{where_str}
ORDER BY DateChek ASC
            """.strip()

            return SQLPlan(
                goal=f"استخراج چک‌های {'دریافتی' if is_recv else 'پرداختی'} با وضعیت {sub}",
                target_tables=[tbl],
                target_columns=["serial", "mab", "DateChek", "Bank", "State"],
                generated_sql=sql,
                validation_status=True,
                row_limit=25
            )

        # 6. Inventory & Stock Levels
        if concept == "inventory_stock":
            sub = intent.sub_concept or "available"
            where = "WHERE Mande > 0"
            order = "Mande DESC"

            if sub == "out_of_stock":
                where = "WHERE Mande <= 0"
                order = "Name ASC"
            elif sub == "low_stock":
                where = "WHERE Mande > 0 AND Mande <= 5"
                order = "Mande ASC"

            sql = f"""
SELECT TOP (25)
    IDKala AS [کد کالا],
    BaghaliCode AS [بارکد],
    Name AS [عنوان کالا],
    Mande AS [موجودی فعلی],
    Bprice AS [فی خرید (ریال)]
FROM dbo.TblKala WITH (NOLOCK)
{where}
ORDER BY {order}
            """.strip()

            return SQLPlan(
                goal=f"استخراج گزارش موجودی انبار (حالت: {sub})",
                target_tables=["TblKala"],
                target_columns=["IDKala", "Name", "Mande", "Bprice"],
                generated_sql=sql,
                validation_status=True,
                row_limit=25
            )

        # 7. Opening Voucher / Trial Balance
        if concept == "trial_balance_or_opening":
            sql = """
SELECT TOP (30)
    tr.Sodor AS [ردیف],
    tr.Srfsl AS [کد کل],
    tr.Moin AS [کد معین],
    tr.HSB AS [کد تفصیلی],
    COALESCE(h.Text, tr.Sharh) AS [شرح حساب],
    tr.Bed AS [بدهکار],
    tr.Bes AS [بستانکار]
FROM dbo.TR tr WITH (NOLOCK)
LEFT JOIN dbo.TblHesabText h WITH (NOLOCK) ON tr.Srfsl = h.Srfsl AND tr.Moin = h.Moin AND tr.HSB = h.HSB
WHERE tr.SanadM = 1
ORDER BY tr.Sodor ASC
            """.strip()

            return SQLPlan(
                goal="استخراج آرتیکل‌ها و تراز سند افتتاحیه سال مالی",
                target_tables=["TR", "TblHesabText"],
                target_columns=["Sodor", "Srfsl", "Moin", "HSB", "Sharh", "Bed", "Bes"],
                generated_sql=sql,
                validation_status=True,
                row_limit=30
            )

        # 8. Sales & Invoices
        if concept == "sales_invoices":
            sql = """
SELECT TOP (25)
    tr.DateR AS [تاریخ فاکتور],
    tr.Factor AS [شماره فاکتور],
    k.Name AS [نام کالا],
    tr.TED AS [تعداد],
    (tr.Bed + tr.Bes) AS [مبلغ فاکتور],
    COALESCE(p.Name, N'مشتری') AS [طرف حساب]
FROM dbo.TR tr WITH (NOLOCK)
LEFT JOIN dbo.TblKala k WITH (NOLOCK) ON tr.Idkala = k.IDKala
LEFT JOIN dbo.TblPerson p WITH (NOLOCK) ON tr.Taraf = p.Sh_ozviat
WHERE tr.Factor > 0
ORDER BY tr.Factor DESC, tr.Sodor DESC
            """.strip()

            return SQLPlan(
                goal="استخراج آخرین فاکتورها و اقلام فروش ثبت‌شده",
                target_tables=["TR", "TblKala", "TblPerson"],
                target_columns=["Factor", "DateR", "Name", "TED", "Bed", "Bes"],
                generated_sql=sql,
                validation_status=True,
                row_limit=25
            )

        # 9. Profit & Loss / Gross Margin Analysis
        if concept == "profit_and_margins":
            sql = """
SELECT TOP (20)
    k.IDKala AS [کد کالا],
    k.Name AS [عنوان کالا],
    SUM(tr.TED) AS [تعداد کل فروش],
    SUM(tr.Bed + tr.Bes) AS [مجموع فروش (ریال)],
    SUM(tr.TED * k.Bprice) AS [بهای تمام شده خرید],
    (SUM(tr.Bed + tr.Bes) - SUM(tr.TED * k.Bprice)) AS [سود ناخالص تقریبی]
FROM dbo.TR tr WITH (NOLOCK)
INNER JOIN dbo.TblKala k WITH (NOLOCK) ON tr.Idkala = k.IDKala
WHERE tr.Factor > 0 AND (tr.Bed + tr.Bes) > 0
GROUP BY k.IDKala, k.Name
HAVING SUM(tr.TED) > 0
ORDER BY [سود ناخالص تقریبی] DESC
            """.strip()

            return SQLPlan(
                goal="تحلیل سود ناخالص و سودآوری اقلام فروش",
                target_tables=["TR", "TblKala"],
                target_columns=["IDKala", "Name", "TED", "Bprice", "Bed", "Bes"],
                generated_sql=sql,
                validation_status=True,
                row_limit=20
            )

        return None
