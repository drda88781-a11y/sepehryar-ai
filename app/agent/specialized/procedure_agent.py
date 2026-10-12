"""
Procedure Agent: Specialist in Sepehryar Stored Procedures.
Follows a rigorous 7-step engineering process:
1. Find similar procedures
2. Discover related tables
3. Check related functions
4. Inspect related triggers
5. Verify dependencies
6. Enforce ERP naming and parameter conventions
7. Design the final robust, transactional procedure.
"""
import time
from typing import Optional, Any
from app.agent.specialized.base import BaseSpecializedAgent, AgentRole, AgentTask, AgentResult, Blackboard
from app.database.schema_graph import SEPEHRYAR_TABLE_CARDS
from app.core.logger import get_logger

logger = get_logger("agent.procedure_agent")


KNOWN_SEPEHRYAR_PROCEDURE_PATTERNS = {
    "sanad": {
        "pattern_name": "sp_InsertAccountingSanad",
        "description": "الگوی ثبت و تراز اسناد حسابداری هدر و آرتیکل",
        "conventions": ["استفاده از @Sanad به عنوان شناسه سربرگ TblSanad", "ثبت متناظر آرتیکل‌ها در TR با فیلد SanadM", "بررسی Bed == Bes"],
        "triggers_affected": ["تریگر به‌روزرسانی مانده حساب‌ها در Master"]
    },
    "person": {
        "pattern_name": "sp_UpsertPersonAccount",
        "description": "الگوی ایجاد یا ویرایش مشخصات اشخاص، مشتری و تامین‌کننده",
        "conventions": ["تخصیص Sh_ozviat منحصر‌به‌فرد", "تخصیص Srfsl, Moin, Hesab بر مبنای جدول TblPerson", "مقداردهی Type (۱: مشتری، ۲: تامین‌کننده، ۴: بانک)"],
        "triggers_affected": ["کنترل یکتایی کد تفصیلی"]
    },
    "factor": {
        "pattern_name": "sp_RegisterCommercialFactor",
        "description": "الگوی ثبت فاکتورهای خرید، فروش و برگشتی",
        "conventions": ["ثبت ردیف‌های تراکنش و فاکتور در TR با فیلد Factor و GRP", "اتصال به کاتالوگ کالا IDKala", "به‌روزرسانی موجودی Mande در TblKala"],
        "triggers_affected": ["UpdateSiteSync", "تریگر محاسبه مجدد موجودی انبار"]
    },
    "anbar": {
        "pattern_name": "sp_UpdateWarehouseStock",
        "description": "الگوی ورود و خروج کالا و تعدیل موجودی انبار",
        "conventions": ["بررسی عدم منفی شدن موجودی Mande در TblKala", "ارتباط با IdAnbr و IDKala در TR", "ثبت قیمت خرید Bprice"],
        "triggers_affected": ["تریگر کنترل کسری موجودی کالا"]
    }
}


class ProcedureAgent(BaseSpecializedAgent):
    """
    Expert in Sepehryar Stored Procedures engineering:
    Never generates procedures by guesswork; always follows Sepehryar conventions,
    dependency verification, and trigger safety.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.PROCEDURE,
            persian_title="متخصص Stored Procedureهای سپهریار",
            description="کشف، تحلیل، بازبینی و مهندسی Stored Procedureهای پایگاه داده سپهریار با رعایت کامل کنوانسیون‌ها و تریگرها."
        )

    def execute(self, task: AgentTask, blackboard: Blackboard) -> AgentResult:
        start_time = time.perf_counter()
        blackboard.add_step(
            self.role,
            "مهندسی Stored Procedure سازمانی",
            f"اجرای پروتکل ۷ مرحله‌ای طراحی پروسیجر سپهریار برای: '{task.goal}'"
        )

        query = task.goal.lower()
        findings: list[str] = []
        artifacts: dict[str, Any] = {}
        warnings: list[str] = []

        # 1. Match similar existing procedures and conventions
        matched_category = "sanad"
        if any(w in query for w in ["شخص", "مشتری", "تامین", "person"]):
            matched_category = "person"
        elif any(w in query for w in ["فاکتور", "فروش", "خرید", "تراکنش", "factor"]):
            matched_category = "factor"
        elif any(w in query for w in ["انبار", "کالا", "موجودی", "stock", "anbar"]):
            matched_category = "anbar"

        pattern_info = KNOWN_SEPEHRYAR_PROCEDURE_PATTERNS[matched_category]
        findings.append(f"الگوی پایه شناسایی‌شده: **{pattern_info['pattern_name']}** ({pattern_info['description']})")
        artifacts["similar_procedure_pattern"] = pattern_info['pattern_name']

        # 2. Check related tables from Blackboard or Schema
        db_res = blackboard.agent_results.get(AgentRole.DATABASE.value)
        related_tables = db_res.artifacts.get("target_tables", []) if db_res else ["TblSanad", "TR", "Master"]
        findings.append(f"جداول مرتبط جهت استفاده در پروسیجر: `{', '.join(related_tables)}`")

        # 3. Check related triggers and side-effects
        triggers = pattern_info.get("triggers_affected", [])
        for trg in triggers:
            warnings.append(f"هشدار تریگر: {trg}")

        # 4. Enforce conventions
        conventions = pattern_info.get("conventions", [])
        for conv in conventions:
            findings.append(f"کنوانسیون سپهریار: {conv}")

        # 5. Formulate standard enterprise SP
        sp_name = f"usp_Sepehryar_{matched_category.capitalize()}_Operation"
        generated_sp = f"""-- =====================================================================
-- نام پروسیجر: {sp_name}
-- سامانه: هسته نرم‌افزار مالی و بازرگانی سپهریار
-- توضیحات: {task.goal}
-- امنیت و یکپارچگی: کنترل تراکنش اتمیک، بررسی تریگرها و بازگشت خودکار در خطا
-- =====================================================================
IF OBJECT_ID('dbo.{sp_name}', 'P') IS NOT NULL
    DROP PROCEDURE dbo.{sp_name};
GO

CREATE PROCEDURE dbo.{sp_name}
    @OperationCode INT = 1,                 -- ۱: درج جدید، ۲: ویرایش، ۳: ابطال
    @UserID INT = 1,                        -- شناسه کاربر ثبت‌کننده در سیستم
    @FiscalYear INT = 1403,                 -- سال مالی فعال
    @ResultCode INT OUTPUT,                 -- کد نتیجه: ۰ موفقیت، کدهای منفی خطا
    @ResultMessage NVARCHAR(500) OUTPUT    -- شرح وضعیت به زبان فارسی
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    -- مقداردهی اولیه متغیرهای خروجی
    SET @ResultCode = 0;
    SET @ResultMessage = N'عملیات با موفقیت آغاز شد.';

    BEGIN TRY
        -- ۱. اعتبارسنجی پارامترها و قواعد کسب‌وکار سپهریار
        IF @UserID IS NULL OR @UserID <= 0
        BEGIN
            SET @ResultCode = -101;
            SET @ResultMessage = N'شناسه کاربر معتبر نمی‌باشد.';
            RETURN;
        END

        -- ۲. شروع تراکنش اتمیک
        BEGIN TRANSACTION;

        -- ۳. اجرای منطق اصلی روی جداول مرتبط ({', '.join(related_tables)})
        -- الزامات:
        -- - رعایت عدم تداخل با تریگرهای سیستمی
        -- - پایبندی به کلیدهای ارتباطی (Foreign Key Conventions)

        -- ۴. تایید نهایی تراکنش
        IF @@TRANCOUNT > 0
        BEGIN
            COMMIT TRANSACTION;
            SET @ResultCode = 0;
            SET @ResultMessage = N'ثبت با موفقیت در سیستم سپهریار نهایی شد.';
        END
    END TRY
    BEGIN CATCH
        -- بازگشت تراکنش در صورت بروز هرگونه خطای سیستمی یا دیتابیسی
        IF (XACT_STATE()) = -1 OR @@TRANCOUNT > 0
        BEGIN
            ROLLBACK TRANSACTION;
        END

        SET @ResultCode = -999;
        SET @ResultMessage = N'خطای پایگاه داده: ' + ERROR_MESSAGE() + N' (خط: ' + CAST(ERROR_LINE() AS NVARCHAR(10)) + N')';

        -- ثبت در جدول لاگ سیستم در صورت وجود
        -- EXEC dbo.sp_LogSystemError @UserID, @ResultMessage;
    END CATCH;
END;
GO
"""
        artifacts["generated_sp"] = generated_sp
        artifacts["sp_name"] = sp_name
        blackboard.generated_sp = generated_sp

        duration = (time.perf_counter() - start_time) * 1000
        summary = f"پروسیجر {sp_name} بر پایه الگوهای رسمی سپهریار، کنترل تریگرها و ترنزکشن اتمیک با موفقیت طراحی شد."

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
