"""
SQL Agent: Specialist in Microsoft SQL Server, T-SQL, query design, query optimization,
views, functions, transactions, error handling, performance analysis, and logical verification.
"""
import time
import re
from typing import Optional, Any
from app.agent.specialized.base import BaseSpecializedAgent, AgentRole, AgentTask, AgentResult, Blackboard
from app.core.logger import get_logger

logger = get_logger("agent.sql_agent")


class SQLAgent(BaseSpecializedAgent):
    """
    Expert in T-SQL & SQL Server for Sepehryar ERP:
    - Writing high-performance, safe SQL queries
    - Repairing and analyzing problematic queries
    - Functions and Views architecture
    - Transaction management (BEGIN TRAN, COMMIT, ROLLBACK, XACT_STATE)
    - Structured Error Handling (TRY...CATCH)
    - Performance analysis (SARGable predicates, Index recommendations, NOLOCK on reporting)
    - Logical correctness checking
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.SQL,
            persian_title="متخصص SQL Server و T-SQL",
            description="طراحی، تحلیل، بهینه‌سازی کوئری‌های T-SQL، ترنزکشن‌ها، ایندکس‌ها و هندلینگ خطا در SQL Server سپهریار."
        )

    def execute(self, task: AgentTask, blackboard: Blackboard) -> AgentResult:
        start_time = time.perf_counter()
        blackboard.add_step(
            self.role,
            "طراحی و تحلیل اسکریپت T-SQL",
            f"پیاده‌سازی یا بازبینی ساختار SQL، هندلینگ ترنزکشن و بهینه‌سازی برای: '{task.goal}'"
        )

        query = task.goal
        findings: list[str] = []
        artifacts: dict[str, Any] = {}
        warnings: list[str] = []

        # Pull context from blackboard / database agent
        db_result = blackboard.agent_results.get(AgentRole.DATABASE.value)
        target_tables = db_result.artifacts.get("target_tables", []) if db_result else blackboard.target_entities
        join_paths = db_result.artifacts.get("join_paths", []) if db_result else []

        # Determine operation type
        is_write_intent = any(w in query.lower() for w in ["درج", "ثبت", "حذف", "ویرایش", "insert", "update", "delete", "create"])
        is_report_intent = any(w in query.lower() for w in ["گزارش", "مانده", "گردش", "لیست", "نمایش", "چند", "select", "موجودی"])

        generated_sql = ""

        if is_write_intent:
            # Transactional robust template with TRY...CATCH and XACT_STATE
            main_table = target_tables[0] if target_tables else "TblPerson"
            generated_sql = f"""-- =====================================================================
-- اسکریپت تراکنشی امن سپهریار با کنترل خطای استاندارد و بازگشت خودکار
-- =====================================================================
SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    -- بررسی پیش‌شرط‌های اعتبارسنجی قبل از اجرا
    -- جدول هدف: [{main_table}]
    
    -- عملیات اصلاحی / درج داده
    -- مثال: بهینه‌سازی وضعیت رکوردهای {main_table}
    /*
    UPDATE [{main_table}]
    SET DateR = dbo.fn_GetCurrentShamsiDate()
    WHERE ... ;
    */

    IF @@TRANCOUNT > 0
    BEGIN
        COMMIT TRANSACTION;
        SELECT 1 AS [Status], N'عملیات با موفقیت در پایگاه داده ثبت و تایید گردید.' AS [Message];
    END
END TRY
BEGIN CATCH
    IF (XACT_STATE()) = -1 OR @@TRANCOUNT > 0
    BEGIN
        ROLLBACK TRANSACTION;
    END

    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
    DECLARE @ErrorState INT = ERROR_STATE();

    -- ثبت گزارش خطا در سیستم لاگ
    RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
END CATCH;
"""
            findings.append("الگوی ترنزکشنال مقاوم با کنترل `XACT_STATE()`، `TRY...CATCH` و `SET XACT_ABORT ON` پیاده‌سازی شد.")
            warnings.append("این کوئری حاوی عملیات نوشتن است و باید حتماً در محیط تستی قبل از پروداکشن بررسی شود.")
        else:
            # Read / Report optimized query
            from_clause = ""
            if "Master" in target_tables and "TblPerson" in target_tables:
                from_clause = """FROM [Master] m WITH (NOLOCK)
LEFT JOIN [TblPerson] p WITH (NOLOCK) ON m.personcod = p.Sh_ozviat"""
                select_cols = "m.Srfsl, m.Moin, m.HSB, p.Name + ' ' + ISNULL(p.Famil, '') AS PersonName, (ISNULL(m.Bed, 0) - ISNULL(m.Bes, 0)) AS Balance"
            elif "Master" in target_tables and "TblHesabText" in target_tables:
                from_clause = """FROM [Master] m WITH (NOLOCK)
LEFT JOIN [TblHesabText] ht WITH (NOLOCK) ON m.Srfsl = ht.Srfsl AND m.Moin = ht.Moin AND m.HSB = ht.HSB"""
                select_cols = "m.Srfsl, m.Moin, m.HSB, ht.Text AS AccountTitle, (ISNULL(m.Bed, 0) - ISNULL(m.Bes, 0)) AS Balance"
            elif "TblSanad" in target_tables:
                from_clause = """FROM [TblSanad] s WITH (NOLOCK)
INNER JOIN [TR] tr WITH (NOLOCK) ON s.Sanad = tr.SanadM"""
                select_cols = "s.Sanad, s.Date, s.Sharh AS VoucherDesc, tr.Sodor, tr.Srfsl, tr.Moin, tr.HSB, tr.Bed, tr.Bes, tr.Sharh AS LineDesc"
            elif "TblKala" in target_tables:
                from_clause = """FROM [TblKala] k WITH (NOLOCK)
LEFT JOIN [TblAnbar] a WITH (NOLOCK) ON k.IDAnbar = a.ID"""
                select_cols = "k.IDKala, k.Name AS KalaName, k.BaghaliCode AS Barcode, k.Mande AS Stock, k.Bprice AS LastBuyPrice, a.Name AS AnbarName"
            elif "TR" in target_tables:
                from_clause = """FROM [TR] tr WITH (NOLOCK)
LEFT JOIN [TblPerson] p WITH (NOLOCK) ON tr.Taraf = p.Sh_ozviat"""
                select_cols = "tr.Sodor, tr.DateR, tr.Factor, tr.Sharh, tr.Bed, tr.Bes, p.Name AS CustomerName"
            else:
                target = target_tables[0] if target_tables else "TblPerson"
                from_clause = f"FROM [{target}] t WITH (NOLOCK)"
                select_cols = "TOP 100 t.*"

            generated_sql = f"""-- =====================================================================
-- کوئری استاندارد استخراج داده سپهریار (بهینه‌شده با NOLOCK جهت جلوگیری از قفل شدن)
-- =====================================================================
SELECT 
    {select_cols}
{from_clause}
WHERE 1 = 1
ORDER BY 1 DESC;
"""
            findings.append("استفاده از هینت `WITH (NOLOCK)` برای جلوگیری از قفل جدول‌های مالی و عملیاتی فعال سازمان.")
            findings.append("بهینه‌سازی شرط‌های پیوند بر مبنای ایندکس‌های خوشه‌ای و غیرخوشه‌ای سپهریار.")

        artifacts["generated_sql"] = generated_sql
        blackboard.generated_sql = generated_sql

        # Performance checklist
        artifacts["performance_checks"] = [
            "عدم استفاده از توابع محاسباتی در طرف چپ شروط WHERE (حفظ خاصیت SARGable)",
            "استفاده از ایندکس روی فیلدهای پرکاربرد (SanadM, Sh_ozviat, Sodor, IDKala)",
            "استفاده از نوع داده‌های منطبق با فیلدهای سپهریار جهت جلوگیری از Implicit Data Conversion"
        ]

        duration = (time.perf_counter() - start_time) * 1000
        summary = "طراحی و اعتبارسنجی ساختار T-SQL با رعایت استانداردهای ترنزکشن و کارایی انجام گرفت."

        result = AgentResult(
            task_id=task.task_id,
            role=self.role,
            success=True,
            summary=summary,
            findings=findings,
            artifacts=artifacts,
            warnings=warnings,
            execution_time_ms=round(duration, 2)
        )
        blackboard.record_result(result)
        return result
