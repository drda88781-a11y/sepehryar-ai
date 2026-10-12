"""
Architecture Agent: Specialist in Sepehryar System Architecture, modular boundaries,
impact analysis, dependency matrices, critical no-touch areas, and risk assessment.
"""
import time
from typing import Optional, Any
from app.agent.specialized.base import BaseSpecializedAgent, AgentRole, AgentTask, AgentResult, Blackboard
from app.core.logger import get_logger

logger = get_logger("agent.architecture_agent")


SEPEHRYAR_MODULES = {
    "financial": {
        "title": "زیرسیستم حسابداری مالی و دفتر کل",
        "core_tables": ["Master", "TblSanad", "TR", "TblHesabText", "TblParam"],
        "critical_rules": ["سند شماره ۱ افتتاحیه است", "تراز بدهکار و بستانکار باید همواره صفر باشد (Bed - Bes == 0)"],
        "no_touch_areas": ["ساختار کدهای کل، معین و تفصیلی", "فرآیند بستن حساب‌های پایان سال مالی"]
    },
    "commercial": {
        "title": "زیرسیستم بازرگانی، خرید و فروش",
        "core_tables": ["TR", "TblTypeTR", "TblPerson"],
        "critical_rules": ["ردیف‌های فاکتور و تراکنش در TR با کد GRP و Factor متناظر می‌شوند", "مبالغ فاکتور بر پایه Bed + Bes یا Ted * Fee محاسبه می‌شود"],
        "no_touch_areas": ["شماره‌گذاری اسناد فاکتور و تریگرهای سینک"]
    },
    "inventory": {
        "title": "زیرسیستم انبار و کاتالوگ کالا",
        "core_tables": ["TblKala", "TblAnbar", "TblBarcode"],
        "critical_rules": ["موجودی Mande باید همگام با تراکنش‌های TR باشد", "کدهای بارکد باید یکتا باشند"],
        "no_touch_areas": ["فرمول میانگین قیمت تمام‌شده کالا"]
    },
    "treasury": {
        "title": "زیرسیستم خزانه‌داری، چک و بانک",
        "core_tables": ["Check", "CheckPardakht", "TblPerson", "Master"],
        "critical_rules": ["بانک‌ها با Type=4 در TblPerson ثبت می‌شوند", "وضعیت چک‌ها با State کنترل می‌شود"],
        "no_touch_areas": ["حساب معین ۱۰۲ و وضعیت چک‌های پاس شده"]
    }
}


class ArchitectureAgent(BaseSpecializedAgent):
    """
    Expert in Sepehryar Enterprise Architecture:
    - Modular placement (Determines which module a feature belongs to)
    - Impact Analysis across tables and services
    - Identifies dependencies
    - Enforces No-Touch Areas (Core parts that must never be altered)
    - Evaluates Risk levels and mitigation strategies
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.ARCHITECTURE,
            persian_title="معمار سیستم و تحلیل‌گر اثرات سپهریار",
            description="تحلیل معماری کلان، جانمایی ماژولار، ماتریس اثر (Impact Analysis)، مناطق غیرقابل تغییر و ارزیابی ریسک."
        )

    def execute(self, task: AgentTask, blackboard: Blackboard) -> AgentResult:
        start_time = time.perf_counter()
        blackboard.add_step(
            self.role,
            "تحلیل معماری کلان و ماتریس اثر",
            f"بررسی جانمایی ماژول، تحلیل اثرات و حوزه‌های ممنوعه برای: '{task.goal}'"
        )

        query = task.goal.lower()
        findings: list[str] = []
        artifacts: dict[str, Any] = {}
        warnings: list[str] = []

        # Determine primary module
        selected_mod = "financial"
        if any(w in query for w in ["کالا", "انبار", "موجودی", "بارکد"]):
            selected_mod = "inventory"
        elif any(w in query for w in ["فاکتور", "فروش", "خرید", "تراکنش"]):
            selected_mod = "commercial"
        elif any(w in query for w in ["چک", "بانک", "خزانه", "صیاد"]):
            selected_mod = "treasury"

        mod_data = SEPEHRYAR_MODULES[selected_mod]
        findings.append(f"جانمایی معماری: قابلیت در **{mod_data['title']}** قرار می‌گیرد.")
        findings.append(f"جداول هسته تحت تاثیر: `{', '.join(mod_data['core_tables'])}`")

        # No touch areas
        no_touch = mod_data["no_touch_areas"]
        for nt in no_touch:
            warnings.append(f"⚠️ بخش غیرقابل تغییر (No-Touch Area): {nt}")

        # Impact analysis
        impacted_subsystems = [mod_data["title"]]
        if selected_mod in ["commercial", "inventory"]:
            impacted_subsystems.append(SEPEHRYAR_MODULES["financial"]["title"])
        if selected_mod == "treasury":
            impacted_subsystems.append(SEPEHRYAR_MODULES["financial"]["title"])

        artifacts["primary_module"] = selected_mod
        artifacts["module_title"] = mod_data["title"]
        artifacts["impacted_subsystems"] = impacted_subsystems
        artifacts["no_touch_areas"] = no_touch

        # Risk assessment
        risk_level = "متوسط (Medium)"
        if "financial" in selected_mod or any(w in query for w in ["حذف", "اصلاح مانده", "بستن"]):
            risk_level = "بالا (High - نیازمند بکاپ و تایید حسابدار ارشد)"
        artifacts["risk_level"] = risk_level
        findings.append(f"سطح ریسک معماری: **{risk_level}**")

        duration = (time.perf_counter() - start_time) * 1000
        summary = f"تحلیل معماری برای ماژول {mod_data['title']} با شناسایی ماتریس اثر و بخش‌های غیرقابل تغییر انجام گرفت."

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
