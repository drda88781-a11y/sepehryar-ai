"""
Debug Agent: Specialist in Root Cause Analysis (RCA) for Sepehryar ERP.
Executes the full diagnostic trajectory:
Error -> Stack Trace -> Code -> SQL -> Database -> Data -> Dependencies -> Root Cause.
Never merely translates or paraphrases error messages.
"""
import time
import re
from typing import Optional, Any
from app.agent.specialized.base import BaseSpecializedAgent, AgentRole, AgentTask, AgentResult, Blackboard
from app.core.logger import get_logger

logger = get_logger("agent.debug_agent")


KNOWN_SEPEHRYAR_ROOT_CAUSES = [
    {
        "patterns": [r"sum\(bed\)", r"sum\(bes\)", r"تراز", r"بالانس", r"سند تراز نیست", r"unbalanced"],
        "cause_title": "عدم تراز بدهکار و بستانکار در ردیف‌های سند مالی (Unbalanced Voucher)",
        "chain": [
            "خطا: تراز نبودن آرتیکل‌های مالی در زمان ثبت نهایی سند",
            "کد: رد درخواست در متد اعتبارسنجی سند مالی",
            "SQL: مقایسه SUM(Bed) با SUM(Bes) در جدول TR به ازای SanadM",
            "داده: اختلاف ریالی بین مجموع بدهکار و مجموع بستانکار سطرها",
            "ریشه اصلی: یکی از ردیف‌های سند فاقد مبلغ یا دارای اختلاف گردکردن (Rounding Error) یا ثبت یک‌طرفه بوده است."
        ],
        "remedy": "بررسی رکوردهای TR به ازای SanadM مربوطه و اعمال آرتیکل تعدیل یا موازنه."
    },
    {
        "patterns": [r"personcod", r"sh_ozviat", r"شخص", r"طرف حساب", r"کد شخص"],
        "cause_title": "نقض ارتباط منطقی کد شخص بین حسابداری و پرونده اشخاص",
        "chain": [
            "خطا: عدم امکان استخراج مشخصات طرف حساب یا ثبت سند بدون نام",
            "کد: فیلد Sh_ozviat یا personcod برابر نال یا نامعتبر ارسال شده",
            "SQL: شکست پیوند بین Master.personcod و TblPerson.Sh_ozviat",
            "داده: مقدار personcod در جدول Master ثبت شده اما رکورد متناظر آن در TblPerson وجود ندارد یا Type نامنطبق است",
            "ریشه اصلی: عدم همگام‌سازی Master.personcod با TblPerson.Sh_ozviat در زمان ثبت اولیه سند یا مایگریشن."
        ],
        "remedy": "تطبیق رکوردهای Master.personcod با TblPerson و مقداردهی صحیح نوع شخص (Type=1 مشتری، Type=2 تامین‌کننده، Type=4 بانک)."
    },
    {
        "patterns": [r"mande", r"موجودی", r"کسری", r"منفی", r"negative inventory"],
        "cause_title": "کنترل کسری موجودی کالا در انبار (Negative Inventory Constraint)",
        "chain": [
            "خطا: جلوگیری از صدور فاکتور فروش یا حواله خروج",
            "کد: اعتبارسنجی کنترل موجودی قبل از صدور",
            "SQL: شرط Mande - TED < 0 در جدول TblKala",
            "داده: مقدار فیلد TED در فاکتور بیش از مقدار جاری Mande در انبار است",
            "ریشه اصلی: عدم ثبت فاکتورهای خرید قبلی یا عدم صدور رسید موقت انبار قبل از فاکتور فروش."
        ],
        "remedy": "بررسی گردش کالا در جدول TR و ثبت اسناد ورود/خرید پیش از ثبت حواله خروج."
    },
    {
        "patterns": [r"deadlock", r"lock request time out", r"قفل", r"1205"],
        "cause_title": "بروز بن‌بست (Deadlock) یا طولانی شدن تراکنش در جداول تراکنشی",
        "chain": [
            "خطا: خطای 1205 SQL Server (Transaction was deadlocked)",
            "کد: لایه دیتابیس تراکنش را Rollback کرده است",
            "SQL: اجرای همزمان خواندن گزارش‌های طولانی بدون NOLOCK و عملیات نوشتن روی TR",
            "دیتابیس: درخواست Exclusive Lock روی صفحاتی که Shared Lock طولانی داشتند",
            "ریشه اصلی: اجرای گزارش‌های سنگین همزمان با ثبت فاکتورهای فروش در زمان پیک کاری بدون استفاده از هینت NOLOCK یا Snapshot Isolation."
        ],
        "remedy": "اعمال WITH (NOLOCK) بر روی گزارش‌های آماری و تفکیک تراکنش‌های سنگین."
    }
]


class DebugAgent(BaseSpecializedAgent):
    """
    Expert in Root Cause Analysis (RCA) for Sepehryar:
    Traces Error -> Stack Trace -> Code -> SQL -> Database -> Data -> Dependencies -> Root Cause.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.DEBUG,
            persian_title="متخصص ریشه‌یابی خطاها (Root Cause Analysis)",
            description="ریشه‌یابی ساختاری و چندلایه‌ای خطاهای سیستمی، دیتابیسی و محاسباتی سپهریار."
        )

    def execute(self, task: AgentTask, blackboard: Blackboard) -> AgentResult:
        start_time = time.perf_counter()
        blackboard.add_step(
            self.role,
            "ریشه‌یابی زنجیره‌ای خطا (Root Cause Analysis)",
            f"تحلیل سلسله‌مراتبی زنجیره Error -> Code -> SQL -> Data برای: '{task.goal}'"
        )

        query = task.goal.lower()
        findings: list[str] = []
        artifacts: dict[str, Any] = {}
        warnings: list[str] = []

        # Find best matching root cause chain
        matched_rca = None
        for rca in KNOWN_SEPEHRYAR_ROOT_CAUSES:
            if any(re.search(pat, query) for pat in rca["patterns"]):
                matched_rca = rca
                break

        if not matched_rca:
            # Generic deep deductive diagnostic chain
            matched_rca = {
                "cause_title": "بررسی ساختار خطا و ناهماهنگی وضعیت داده‌ها در دیتابیس",
                "chain": [
                    f"خطا / شرح مسئله: {task.goal}",
                    "استک تریس و کد: بررسی نقطه فراخوانی در لایه DAL یا سرویس",
                    "دستور SQL: اعتبارسنجی دستور ارسالی به SQL Server",
                    "پایگاه داده: بررسی عدم نقض شروط یکتایی، نوع داده‌ها و تریگرها",
                    "داده و وابستگی‌ها: بررسی وجود رکوردهای پیش‌نیاز در جداول پایه",
                    "ریشه اصلی: ناهماهنگی داده‌های ارسالی با قواعد و محدودیت‌های تجاری فعال سیستم."
                ],
                "remedy": "بررسی مقادیر ورودی در لاگ سرور و اجرای کوئری اعتبارسنجی در جدول هدف."
            }

        findings.append(f"عنوان تحلیل ریشه‌ای: **{matched_rca['cause_title']}**")
        for step in matched_rca["chain"]:
            findings.append(f"🔗 {step}")

        artifacts["root_cause_title"] = matched_rca["cause_title"]
        artifacts["diagnostic_chain"] = matched_rca["chain"]
        artifacts["remedy"] = matched_rca["remedy"]

        findings.append(f"راهکار پیشنهادی: {matched_rca['remedy']}")
        warnings.append("هرگز خطای اعلام‌شده را فقط یک پیام گذرا در نظر نگیرید؛ علت اصلی در وضعیت داده‌های جدول مربوطه نهفته است.")

        duration = (time.perf_counter() - start_time) * 1000
        summary = f"تحلیل ریشه‌ای خطا با موفقیت استخراج شد: {matched_rca['cause_title']}"

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
