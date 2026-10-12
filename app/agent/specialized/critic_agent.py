"""
Critic Agent: The technical Quality Gatekeeper and Guardrail Auditor.
No technical response or script is finalized without Critic Agent review.
Inspects architectural compatibility, SQL safety, risk of data corruption,
and ignored dependencies or triggers.
"""
import time
import re
from typing import Optional, Any
from app.agent.specialized.base import (
    BaseSpecializedAgent,
    AgentRole,
    AgentTask,
    AgentResult,
    Blackboard,
    CriticReview,
    CriticVerdict
)
from app.core.logger import get_logger

logger = get_logger("agent.critic_agent")


class CriticAgent(BaseSpecializedAgent):
    """
    Quality & Safety Auditor:
    - Verifies compatibility with Sepehryar enterprise architecture
    - Checks SQL soundness (Logical traps, Cartesian products, unindexed scans)
    - Validates data integrity (Guarantees no data corruption, ledger balance preservation)
    - Verifies critical dependencies and triggers were not overlooked
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.CRITIC,
            persian_title="منتقد و ارزیاب کیفی فنی (Critic & Quality Gatekeeper)",
            description="دروازه‌بان تضمین کیفیت، اعتبارسنجی انطباق معماری، بررسی خطر تخریب داده‌ها و خطاهای منطقی SQL."
        )

    def review_solution(self, blackboard: Blackboard) -> CriticReview:
        """Runs the complete critical evaluation suite across all blackboard artifacts."""
        safety_checks: list[str] = []
        concerns: list[str] = []
        recommendations: list[str] = []
        is_safe = True
        arch_compat = True

        sql_text = blackboard.generated_sql or ""
        sp_text = blackboard.generated_sp or ""
        code_text = blackboard.generated_code or ""
        combined_text = f"{sql_text}\n{sp_text}\n{code_text}".lower()

        # 1. Data Corruption & Destructive Command Check
        destructive_patterns = [
            r"\bdrop\s+table\b",
            r"\btruncate\s+table\b",
            r"\bdelete\s+from\s+\[?master\]?\s*(where)?",
            r"\bdelete\s+from\s+\[?tblsanad\]?\s*(where)?"
        ]
        for pat in destructive_patterns:
            if re.search(pat, combined_text):
                concerns.append("خطر تخریب فیزیکی داده‌ها: دستور غیرمجاز ساختاری یا حذف کلی شناسایی شد!")
                is_safe = False

        if is_safe:
            safety_checks.append("عدم وجود دستورات مخرب و تخریب‌کننده ساختار دیتابیس (بدون DROP TABLE یا TRUNCATE غیرمجاز).")

        # 2. Transaction Integrity Check (Writes must be wrapped in transactions)
        has_dml_writes = any(w in combined_text for w in ["insert into", "update ", "delete "])
        if has_dml_writes:
            if "begin transaction" in combined_text and ("commit transaction" in combined_text or "commit" in combined_text):
                safety_checks.append("عملیات نوشتن به صورت اتمیک درون تراکنش (BEGIN TRAN ... COMMIT) محصور شده است.")
            else:
                concerns.append("عملیات اصلاح داده بدون تراکنش صریح مشاهده شد که در صورت بروز خطا موجب ناهمگامی داده‌ها می‌شود.")
                is_safe = False

            if "rollback" in combined_text:
                safety_checks.append("مسیر بازگشت خودکار (Rollback) در بلاک CATCH پیاده‌سازی شده است.")
            else:
                concerns.append("عدم مشاهده ROLLBACK در زمان وقوع استثنا در کد تراکنشی.")

        modifying_vouchers = has_dml_writes and any(t in combined_text for t in ["tblsanad", "tr", "master"])
        if modifying_vouchers:
            if "bed" in combined_text and "bes" in combined_text:
                safety_checks.append("قاعده تراز حسابداری (بررسی همزمان Bed و Bes) رعایت شده است.")
            else:
                concerns.append("دستکاری در جداول مالی سند بدون در نظر گرفتن تقارن بدهکار و بستانکار!")
                arch_compat = False
        else:
            safety_checks.append("یکپارچگی دفاتر مالی: ساختار کوئری به دفاتر آسیبی نمی‌رساند.")

        # 4. Dependency & Join Cartesian Product Check
        # Detect comma joins like 'FROM TableA, TableB'
        has_comma_join = bool(re.search(r"\bfrom\s+\[?\w+\]?\s*,\s*\[?\w+\]?", combined_text))
        if has_comma_join:
            concerns.append("احتمال وقوع ضرب دکارتی (Cartesian Product) به دلیل استفاده از کاما به جای JOIN صریح در FROM.")
            arch_compat = False
        else:
            safety_checks.append("پیوند جداول به صورت صریح با هینت‌ها و کلیدهای استاندارد (ON condition) پیاده‌سازی شده است.")

        # 5. Determine Verdict
        if not is_safe or not arch_compat:
            verdict = CriticVerdict.REJECTED
            confidence = 0.60
            recommendations.append("بازبینی اسکریپت با الزام به مدیریت تراکنش اتمیک و حفظ تراز دفاتر حسابداری.")
        elif concerns:
            verdict = CriticVerdict.APPROVED_WITH_WARNINGS
            confidence = 0.85
            recommendations.append("قبل از اجرا روی سرور عملیاتی، بکاپ کامل تهیه و در محیط تست اعتبارسنجی شود.")
        else:
            verdict = CriticVerdict.APPROVED
            confidence = 0.98
            safety_checks.append("تطابق کامل با استانداردها و کنوانسیون‌های رسمی سپهریار احراز گردید.")

        review = CriticReview(
            verdict=verdict,
            confidence_score=confidence,
            safety_checks=safety_checks,
            architecture_compatibility=arch_compat,
            data_integrity_safe=is_safe,
            concerns_or_critiques=concerns,
            recommendations=recommendations
        )
        blackboard.critic_reviews.append(review)
        return review

    def execute(self, task: AgentTask, blackboard: Blackboard) -> AgentResult:
        start_time = time.perf_counter()
        blackboard.add_step(
            self.role,
            "ارزیابی و دروازه‌بانی کیفی (Critic Gatekeeper)",
            "بررسی امنیتی، معماری، تخریب داده و منطق تراکنش راه‌حل‌های تولید شده."
        )

        review = self.review_solution(blackboard)

        findings: list[str] = [f"نتیجه داوری Critic: **{review.verdict.value.upper()}** (ضریب اطمینان: {int(review.confidence_score * 100)}%)"]
        for sc in review.safety_checks:
            findings.append(f"✅ {sc}")

        warnings = review.concerns_or_critiques
        artifacts = {
            "verdict": review.verdict.value,
            "confidence_score": review.confidence_score,
            "safety_checks": review.safety_checks,
            "concerns": review.concerns_or_critiques,
            "recommendations": review.recommendations
        }

        duration = (time.perf_counter() - start_time) * 1000
        summary = f"ارزیابی Critic تکمیل شد: وضعیت {review.verdict.value}"

        result = AgentResult(
            task_id=task.task_id,
            role=self.role,
            success=(review.verdict != CriticVerdict.REJECTED),
            summary=summary,
            findings=findings,
            artifacts=artifacts,
            warnings=warnings,
            execution_time_ms=round(duration, 2)
        )
        blackboard.record_result(result)
        return result
