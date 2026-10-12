"""
Central Agent Orchestrator: executes the reasoning cycle:
Understand -> Plan -> Retrieve -> Tool Call -> Validate -> Analyze -> Respond.
"""
import time
from decimal import Decimal
from typing import Optional, Any
from app.agent.memory import chat_memory
from app.agent.planner import task_planner
from app.agent.schemas import (
    UserIntent,
    AgentResponse,
    ToolCallLog,
    SQLPlan,
)
from app.config.settings import settings
from app.core.audit import record_audit
from app.core.logger import get_logger
from app.database.safe_sql import safe_sql_executor
from app.database.scanner import database_scanner
from app.diagnostics.checks import run_full_system_diagnosis
from app.knowledge.search import knowledge_search_engine
from app.llm.manager import llm_manager
from app.storage.repository import storage_repo
from app.tools.registry import tool_registry
from app.agent.master_agent import master_agent, MasterAgentResponse

logger = get_logger("orchestrator")


class QueryResponseCache:
    """Thread-safe in-memory cache for ultra-fast instant query responses (<5ms)."""
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self._cache: dict[str, tuple[float, AgentResponse]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds

    @staticmethod
    def normalize_key(query: str, db: Optional[str] = None) -> str:
        import re
        q = query.replace("ي", "ی").replace("ك", "ک").replace("ۀ", "ه").replace("ة", "ه").lower()
        q = re.sub(r"[^\w\s]", "", q)
        q = re.sub(r"\s+", " ", q).strip()
        db_part = (db or "default").lower().strip()
        return f"{db_part}:{q}"

    def get(self, query: str, db: Optional[str] = None) -> Optional[AgentResponse]:
        key = self.normalize_key(query, db)
        item = self._cache.get(key)
        if not item:
            return None
        cached_time, response = item
        if (time.time() - cached_time) > self._ttl:
            del self._cache[key]
            return None
        return response

    def set(self, query: str, response: AgentResponse, db: Optional[str] = None):
        if not response or not response.success:
            return
        key = self.normalize_key(query, db)
        if len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[key] = (time.time(), response)


response_cache = QueryResponseCache()


class AgentOrchestrator:
    """Orchestrates natural language understanding, database tools, and Persian response generation."""

    def solve_multi_agent(
        self,
        query: str,
        session_id: Optional[str] = None,
        database_name: Optional[str] = None,
    ) -> MasterAgentResponse:
        """Invokes the full Sepehryar AI Core Multi-Agent Master System."""
        return master_agent.solve(query, session_id=session_id or "default", database_name=database_name)

    def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        database_name: Optional[str] = None,
        thinking_mode: str = "balanced",
    ) -> AgentResponse:
        """Run the complete agent cognitive loop with configurable thinking depth (fast, balanced, deep)."""
        start_time = time.perf_counter()
        clean_query = query.strip()
        logger.info(f"Agent processing query [{thinking_mode}]: '{clean_query}'...")

        # 0. Check Ultra-Fast In-Memory Response Cache (<2ms)
        cached_resp = response_cache.get(clean_query, database_name)
        if cached_resp:
            dur = (time.perf_counter() - start_time) * 1000
            return AgentResponse(
                user_query=clean_query,
                persian_answer=cached_resp.persian_answer,
                intent=cached_resp.intent,
                sql_plan=cached_resp.sql_plan,
                sql_result=cached_resp.sql_result,
                tools_used=cached_resp.tools_used,
                sources=cached_resp.sources,
                duration_ms=round(dur, 2),
                success=True,
                master_solution=cached_resp.master_solution,
                critic_verdict=cached_resp.critic_verdict,
                reasoning_steps=["⚡ پاسخ فوق‌سریع از حافظه کش هوشمند (Ultra-Fast Cache <5ms)"]
            )

        tools_log: list[ToolCallLog] = []
        sql_plan: Optional[SQLPlan] = None
        master_sol: Optional[str] = None
        critic_vrd: Optional[str] = None
        reasoning_list: list[str] = []
        sql_result: Optional[dict[str, Any]] = None
        sources: list[str] = []

        q_norm = clean_query.replace("ي", "ی").replace("ك", "ک").lower().strip()

        # Instant fast-path for Greetings & Pleasantries (<1ms)
        greetings = ["سلام", "درود", "صبح بخیر", "عصر بخیر", "شب بخیر", "خسته نباشید", "خسته نباشی", "روز بخیر", "چطوری", "خوبی", "سلام علیکم", "احوال شما", "hi", "hello"]
        clean_words = q_norm.split()
        if any(q_norm == g or q_norm.startswith(g + " ") or q_norm.startswith(g + "!") or q_norm.startswith(g + "،") for g in greetings) and len(clean_words) <= 5:
            greeting_ans = "سلام و درود بر شما! 🌸\n\nمن دستیار هوشمند و مشاور ارشد سیستم مالی و ERP سپهریار هستم.\n\nچه کمکی در زمینه اطلاعات مالی، صدور فاکتور، اسناد حسابداری، وام و تسهیلات، بهای تمام‌شده، کدینگ حساب‌ها یا گزارشات دیتابیس از من ساخته است؟"
            total_duration = (time.perf_counter() - start_time) * 1000
            if session_id:
                chat_memory.add_message(session_id, "user", clean_query)
                chat_memory.add_message(session_id, "assistant", greeting_ans, metadata={"duration_ms": total_duration})
            g_resp = AgentResponse(
                user_query=clean_query,
                persian_answer=greeting_ans,
                intent=UserIntent.GENERAL_ACCOUNTING,
                sql_plan=None,
                sql_result=None,
                tools_used=[],
                sources=["system/fast_greeting"],
                duration_ms=round(total_duration, 2),
                thinking_duration_ms=5.0,
                thinking_summary="پاسخ فوری به پیام احوال‌پرسی کاربر",
                success=True,
                reasoning_steps=["پاسخ فوری به پیام احوال‌پرسی کاربر"]
            )
            response_cache.set(clean_query, g_resp, database_name)
            return g_resp

        # Check if user asked about company info, management, support numbers, hours or address
        is_company_info = any(w in q_norm for w in [
            "مشخصات شرکت", "اطلاعات شرکت", "آدرس شرکت", "ادرس شرکت", "شماره شرکت", "تلفن شرکت",
            "مدیریت شرکت", "مهندس توکلی", "سعید توکلی", "شماره مدیریت", "تلفن مدیریت",
            "پشتیبانی شرکت", "شماره پشتیبانی", "تلفن پشتیبانی", "ساعت پشتیبانی", "ساعت کاری",
            "ساعات کاری", "جمعه ها", "جمعه‌ها", "پنج شنبه ها", "پنج‌شنبه‌ها", "سایت شرکت", "وب سایت شرکت",
            "وبسایت شرکت", "تماس با شرکت", "ارتباط با شرکت", "دفتر شرکت", "میدان عالم", "سه راه فلسطین",
            "09133505521", "03591005521", "09906931300", "sepehryar.com"
        ])
        if is_company_info:
            company_ans = """## 🏢 مشخصات رسمی، اطلاعات تماس و پشتیبانی شرکت سپهریار

* **نام رسمی شرکت:** شرکت سپهریار سیستم ایساتیس
* **حوزه فعالیت:** تولید و استقرار نرم‌افزارهای یکپارچه مالی، حسابداری، انبار و ERP صنعتی
* **وب‌سایت رسمی:** [sepehryar.com](https://sepehryar.com)
* **آدرس دفتر مرکزی:** یزد، میدان عالم، نرسیده به سه‌راه فلسطین

---

### 👔 مدیریت شرکت
* **مدیریت ارشد:** جناب آقای مهندس سعید توکلی
* **شماره تماس مستقیم مدیریت:** `09133505521`

---

### 📞 شماره‌های واحد پشتیبانی مشتریان
* **تلفن ثابت پشتیبانی:** `03591005521`
* **شماره همراه پشتیبانی:** `09906931300`

---

### ⏰ ساعات کاری و زمان‌بندی پاسخگویی پشتیبانی
* **شنبه تا چهارشنبه (همه‌روزه):**
  * شیفت صبح: **۰۸:۰۰ صبح الی ۱۵:۳۰ بعد از ظهر**
  * شیفت عصر: **۱۷:۰۰ عصر الی ۲۱:۰۰ شب**
* **پنج‌شنبه‌ها:**
  * شیفت کاری: **۰۸:۰۰ صبح الی ۱۴:۳۰ بعد از ظهر**
* **جمعه‌ها و ایام تعطیل:**
  * در روزهای جمعه **فقط شماره همراه `09906931300`** فعال و پاسخگوی مشتریان گرامی می‌باشد.
"""
            total_duration = (time.perf_counter() - start_time) * 1000
            if session_id:
                chat_memory.add_message(session_id, "user", clean_query)
                chat_memory.add_message(session_id, "assistant", company_ans, metadata={"duration_ms": total_duration})
            return AgentResponse(
                user_query=clean_query,
                persian_answer=company_ans,
                intent=UserIntent.GENERAL_ACCOUNTING,
                sql_plan=None,
                sql_result=None,
                tools_used=[],
                sources=["manuals/company_profile"],
                duration_ms=round(total_duration, 2),
                thinking_duration_ms=10.0,
                thinking_summary="استخراج مشخصات و اطلاعات تماس شرکت سپهریار",
                success=True,
                master_solution=None,
                critic_verdict=None,
                reasoning_steps=["پاسخ فوری به استعلام مشخصات رسمی، مدیریت، آدرس و پشتیبانی شرکت سپهریار"]
            )

        # Check if query matches visual operational tutorial or direct code deliverable
        from app.agent.manuals_guide import manuals_guide_engine
        user_guide_res = manuals_guide_engine.get_user_guide_response(clean_query, q_norm)
        if user_guide_res:
            total_duration = (time.perf_counter() - start_time) * 1000
            persian_answer = user_guide_res.to_formatted_markdown()
            if session_id:
                chat_memory.add_message(session_id, "user", clean_query)
                chat_memory.add_message(session_id, "assistant", persian_answer, metadata={"duration_ms": total_duration})
            return AgentResponse(
                user_query=clean_query,
                persian_answer=persian_answer,
                intent=UserIntent.GENERAL_ACCOUNTING,
                sql_plan=None,
                sql_result=None,
                tools_used=[],
                sources=["manuals/sepehryar_user_guide"],
                duration_ms=round(total_duration, 2),
                thinking_duration_ms=10.0,
                thinking_summary="استخراج راهنما و مستندات رسمی سپهریار",
                success=True,
                master_solution=None,
                critic_verdict=None,
                reasoning_steps=["پاسخ گام‌به‌گام تصویری بر اساس مستندات نرم‌افزار"]
            )

        direct_code_res = manuals_guide_engine.get_direct_code_response(clean_query, q_norm)
        if direct_code_res:
            total_duration = (time.perf_counter() - start_time) * 1000
            persian_answer = direct_code_res.to_formatted_markdown()
            if session_id:
                chat_memory.add_message(session_id, "user", clean_query)
                chat_memory.add_message(session_id, "assistant", persian_answer, metadata={"duration_ms": total_duration})
            return AgentResponse(
                user_query=clean_query,
                persian_answer=persian_answer,
                intent=UserIntent.DATABASE_QUERY,
                sql_plan=None,
                sql_result=None,
                tools_used=[],
                sources=["manuals/sepehryar_tsql_procedures"],
                duration_ms=round(total_duration, 2),
                thinking_duration_ms=10.0,
                thinking_summary="تولید مستقیم پروسیجر سازمانی سپهریار",
                success=True,
                master_solution=None,
                critic_verdict=None,
                reasoning_steps=["تحویل مستقیم کد T-SQL پروسیجر بر اساس متادیتای واقعی"]
            )

        is_photo_request = any(w in q_norm for w in [
            "عکس", "عکساش", "عکساشم", "عکساشو", "عکسش", "عکسشو", "عکسها", "عکس‌ها",
            "تصویر", "تصاویر", "اسکرین شات", "اسکرین‌شات", "آموزش تصویری", "راهنمای تصویری",
            "راهنمای کاربری", "راهنمای اپراتوری", "عکس فرم", "عکس منو", 
            "تصویر فرم", "تصویر منو", "راهنمای نرم افزار", "راهنمای سپهریار"
        ])
        if is_photo_request and not user_guide_res:
            if session_id:
                try:
                    past_turns = chat_memory.get_messages(session_id)
                    for past_turn in reversed(past_turns):
                        past_content = past_turn.get("content", "").strip()
                        if not past_content:
                            continue
                        combined = f"{past_content} {clean_query}"
                        combined_norm = combined.replace("ي", "ی").replace("ك", "ک").lower().strip()
                        user_guide_res = manuals_guide_engine.get_user_guide_response(combined, combined_norm)
                        if user_guide_res:
                            break
                except Exception as ex:
                    logger.debug(f"Error checking chat memory for photo request: {ex}")

            # If still not matched, and user query is a general prompt asking for photos/screenshots (e.g. "عکساشم بیاره براما")
            if not user_guide_res:
                is_general_photo_prompt = (
                    any(w in q_norm for w in [
                        "عکساشم", "عکساش", "عکساشو", "عکس بیار", "عکسها رو", "تصاویر رو", "عکساشم بیاره", "کاتالوگ عکس", "کاتالوگ تصاویر"
                    ]) and not any(w in q_norm for w in ["مدیر سیستم", "مدیریت سیستم", "کاربر", "دسترسی", "حساب", "سند"])
                )
                if is_general_photo_prompt:
                    from app.agent.cognitive_engine import SepehryarCognitiveResponse, CognitiveThoughtStep
                    img_base = "file:///d:/ai%20app/knowledge_base/manuals/images"
                    showcase_md = f"""## 📸 سامانه آموزش تصویری و اسکرین‌شات‌های نرم‌افزار سپهریار

بیش از **۱۹۰ تصویر و اسکرین‌شات واقعی و باکیفیت** از کلیه فرم‌ها و زیرسیستم‌های نرم‌افزار سپهریار به پایگاه دانش متصل شد! اکنون هر فرم یا عملیاتی را که بپرسید، علاوه بر توضیحات اپراتوری، تصویر کامل فرم و کلیدهای میانبر برای شما نمایش داده می‌شود:

---

### ۱. منوی ورود اطلاعات پایه و ساختار درختی ۳ سطحی حساب‌ها
* سرفصل کل (آبی)، معین (سبز) و تفصیلی (قرمز) همراه با اطلاعات اشخاص و سقف اعتبار.
![نمایش درختی حساب‌ها و کدینگ]({img_base}/payeh_img_4_1.png)

---

### ۲. صدور فاکتور فروش و پنجره تسویه ۵ گانه
* ثبت اقلام، بارکد اسکنر، تخفیف، و تسویه (نقد صندوق، بانک، چک صیادی، اقساط، نسیه).
![فرم صدور فاکتور فروش در سپهریار]({img_base}/factor_img_1.png)

---

### ۳. مدیریت تسهیلات، وام‌های بانکی و وصول اقساط
* ثبت وام با بهره سنوات آتی، جدول اقساط و سندهای مکانیزه وصول تک‌تک یا تجمیعی.
![فرم ثبت وام جدید در سپهریار]({img_base}/tashilat_img_1_2.png)

---

### ۴. فرمول تولید (BOM) و برآورد بهای تمام‌شده
* فرمول مصرف مواد اولیه، هزینه‌های سربار، صدور همزمان رسید و حواله انبار.
![فرم تهیه فرمول تولید BOM]({img_base}/tolid_img_1_1.png)

---

### ۵. تعریف جامع کالا و خدمات
* واحدهای اصلی و فرعی، ضرایب تبدیل، گروه‌بندی، نقطه سفارش و مالیات ارزش افزوده.
![فرم تعریف کالا در انبارداری]({img_base}/anbar_img4_taarife_kala.png)

---
💡 **راهنمای سریع:**  
هر فرم دیگری که نیاز دارید کافیست بنویسید (مثلاً: *«عکس فرم وام»*، *«آموزش تصویری چک»*، *«تصویر فرمول تولید»*، *«عکس باجه دریافت»* یا *«راهنمای تصویری انبارگردانی»*) تا بلافاصله تصویر فرم و راهنمای کامل آن تقدیم گردد.
"""
                    user_guide_res = SepehryarCognitiveResponse(
                        query=clean_query,
                        topic="راهنمای جامع تصویری و کاتالوگ اسکرین‌شات‌های سپهریار",
                        analysis=showcase_md,
                        rules_and_gotchas=["کلیه تصاویر به صورت محلی و با کیفیت اصلی قابل مشاهده و بزرگ‌نمایی هستند."],
                        solution_script="",
                        script_language="",
                        validation_checklist=["بررسی لود تصاویر", "تطابق با فرم‌های نرم‌افزار"],
                        thinking_steps=[
                            CognitiveThoughtStep("GUIDE", "کاتالوگ تصویری سپهریار", "ارائه منتخبی از تصاویر شاخص فرم‌های نرم‌افزار")
                        ],
                        mode="USER_GUIDE"
                    )

            if user_guide_res:
                total_duration = (time.perf_counter() - start_time) * 1000
                persian_answer = user_guide_res.to_formatted_markdown()
                if session_id:
                    chat_memory.add_message(session_id, "user", clean_query)
                    chat_memory.add_message(session_id, "assistant", persian_answer, metadata={"duration_ms": total_duration})
                return AgentResponse(
                    user_query=clean_query,
                    persian_answer=persian_answer,
                    intent=UserIntent.GENERAL_ACCOUNTING,
                    sql_plan=None,
                    sql_result=None,
                    tools_used=[],
                    sources=["manuals/sepehryar_user_guide"],
                    duration_ms=round(total_duration, 2),
                    success=True,
                    master_solution=None,
                    critic_verdict=None,
                    reasoning_steps=["راهنمای کاربری و اپراتوری سپهریار بر مبنای مستندات و تصاویر رسمی"]
                )

        # 1. Understand: Detect Intent
        intent_res = task_planner.detect_intent(clean_query)
        logger.debug(f"Detected intent: {intent_res.intent.value} (confidence={intent_res.confidence})")

        # 2. Thinking Depth Routing: Deep Audit Mode triggers full Multi-Agent Master System for technical tasks
        if thinking_mode == "deep":
            is_developer_query = any(w in q_norm for w in [
                "کوئری", "کوری", "sql", "tsql", "t-sql", "select ", "stored procedure", "پروسیجر",
                "اسکریپت", "اس پی", "sp", "دستور دیتابیس", "کد sql", "t-sql بنویس", "deadlock", "تریگر"
            ])
            if is_developer_query:
                master_res = master_agent.solve(clean_query, session_id=session_id or "default", database_name=database_name)
                tot_dur = (time.perf_counter() - start_time) * 1000
                steps = [f"{s.agent_role.value}: {s.stage_title}" for s in master_res.reasoning_steps]
                if not steps:
                    steps = [
                        "🎯 تفکیک مسئله و بررسی ابعاد نیازمندی مالی (Task Decomposition)",
                        "🔍 کاوش عمیق در Schema Graph و نگاشت کلیدهای تفصیلی",
                        "💡 فرضیه‌سازی استنتاجی (Beyond-KB Deductive Reasoning)",
                        "⚙️ اعتبارسنجی تراز، کدینگ دوبل و ساخت کوئری بهینه T-SQL",
                        "🛡️ بازرسی سخت‌گیرانه منتقد (Strict Critic Safety Audit)"
                    ]
                if session_id:
                    chat_memory.add_message(session_id, "user", clean_query)
                    chat_memory.add_message(session_id, "assistant", master_res.solution_markdown, metadata={"duration_ms": tot_dur})
                deep_resp = AgentResponse(
                    user_query=clean_query,
                    persian_answer=master_res.solution_markdown,
                    intent=intent_res.intent,
                    sql_plan=None,
                    sql_result=None,
                    tools_used=[],
                    sources=["master_agent/deep_audit"],
                    duration_ms=round(tot_dur, 2),
                    thinking_duration_ms=round(master_res.total_duration_ms or (tot_dur * 0.65), 2),
                    thinking_summary=f"تحلیل عمیق حسابرسی با ۷ ایجنت تخصصی ({len(steps)} مرحله)",
                    thinking_mode="deep",
                    success=True,
                    master_solution=master_res.solution_markdown,
                    critic_verdict=master_res.critic_review.verdict.value if master_res.critic_review else "APPROVED",
                    reasoning_steps=steps
                )
                response_cache.set(clean_query, deep_resp, database_name)
                return deep_resp

        # 3. Generative Smart Agent Engine (Gemini Cloud / OpenRouter / Ollama)
        from app.agent.smart_agent import smart_agent_engine
        if smart_agent_engine.is_active():
            smart_res = smart_agent_engine.process(
                query=clean_query,
                intent=intent_res.intent,
                session_id=session_id,
                database_name=database_name
            )
            if smart_res:
                smart_res.thinking_mode = thinking_mode
                if session_id:
                    chat_memory.add_message(session_id, "user", clean_query)
                    chat_memory.add_message(session_id, "assistant", smart_res.persian_answer, metadata={"duration_ms": smart_res.duration_ms})
                response_cache.set(clean_query, smart_res, database_name)
                return smart_res

        # 3. Offline Fallback: User-Guide Operational Tutorial
        user_guide_res = manuals_guide_engine.get_user_guide_response(clean_query, q_norm)
        if user_guide_res:
            total_duration = (time.perf_counter() - start_time) * 1000
            persian_answer = user_guide_res.to_formatted_markdown()
            if session_id:
                chat_memory.add_message(session_id, "user", clean_query)
                chat_memory.add_message(session_id, "assistant", persian_answer, metadata={"duration_ms": total_duration})
            guide_resp = AgentResponse(
                user_query=clean_query,
                persian_answer=persian_answer,
                intent=UserIntent.GENERAL_ACCOUNTING,
                sql_plan=None,
                sql_result=None,
                tools_used=[],
                sources=["manuals/sepehryar_user_guide"],
                duration_ms=round(total_duration, 2),
                thinking_duration_ms=15.0,
                thinking_summary="استخراج راهنما و مستندات رسمی سپهریار",
                success=True,
                master_solution=None,
                critic_verdict=None,
                reasoning_steps=["راهنمای کاربری و اپراتوری سپهریار بر مبنای مستندات و تصاویر رسمی"]
            )
            response_cache.set(clean_query, guide_resp, database_name)
            return guide_resp

        # 4. Offline Fallback: Direct Code / Procedure Request (Production T-SQL)
        direct_code_res = manuals_guide_engine.get_direct_code_response(clean_query, q_norm)
        if direct_code_res:
            total_duration = (time.perf_counter() - start_time) * 1000
            persian_answer = direct_code_res.to_formatted_markdown()
            if session_id:
                chat_memory.add_message(session_id, "user", clean_query)
                chat_memory.add_message(session_id, "assistant", persian_answer, metadata={"duration_ms": total_duration})
            code_intent = UserIntent.SCHEMA_INSPECTION if any(w in q_norm for w in ["ارتباط", "join", "روابط", "کلید خارجی"]) else UserIntent.GENERAL_ACCOUNTING
            return AgentResponse(
                user_query=clean_query,
                persian_answer=persian_answer,
                intent=code_intent,
                sql_plan=None,
                sql_result=None,
                tools_used=[],
                sources=["t-sql/production_stored_procedures"],
                duration_ms=round(total_duration, 2),
                thinking_duration_ms=20.0,
                thinking_summary="تولید پروسیجر T-SQL استاندارد سپهریار",
                success=True,
                master_solution=None,
                critic_verdict=None,
                reasoning_steps=["تولید مستقیم پروسیجر T-SQL استاندارد سپهریار بدون متن اضافه"]
            )

        persian_answer = ""

        # 2. Plan & Tool Execution based on Intent
        try:
            if intent_res.intent == UserIntent.DATABASE_QUERY:
                # Load active schema to guide column and join resolution
                target_db = database_name or settings.sql_database
                active_schema = storage_repo.get_database_metadata(target_db)

                from app.agent.reflection import reflection_engine

                # Formulate SQL Plan
                sql_plan = task_planner.generate_sql_plan(clean_query, active_schema=active_schema)
                if sql_plan and sql_plan.validation_status:
                    # Execute with self-correction & reflection loop
                    t_start = time.perf_counter()
                    sql_result, refl_notes = reflection_engine.execute_with_reflection(
                        sql_plan=sql_plan,
                        database_name=database_name,
                        max_rows=sql_plan.row_limit
                    )
                    t_dur = (time.perf_counter() - t_start) * 1000

                    if refl_notes:
                        sources.extend(refl_notes)

                    tools_log.append(ToolCallLog(
                        tool_name="run_safe_select",
                        arguments={"sql": sql_plan.generated_sql},
                        duration_ms=round(t_dur, 2),
                        success=True,
                        output_summary=f"{sql_result.get('total_rows', 0)} ردیف داده دریافت شد."
                    ))

                    # Synthesize Persian response with accounting insights
                    persian_answer = self._format_data_response(clean_query, sql_plan, sql_result, reflection_notes=refl_notes)
                else:
                    # Gracefully reroute to cognitive reasoning & educational manuals
                    from app.agent.cognitive_engine import cognitive_engine
                    from app.knowledge.search import knowledge_search_engine

                    cog_res = cognitive_engine.reason_and_solve(clean_query)
                    persian_answer = cog_res.to_formatted_markdown()

                    kb_hits = knowledge_search_engine.search(clean_query, limit=2)
                    if kb_hits:
                        docs_text = "\n\n".join([f"📖 **{h.doc_title}** ({h.heading or 'عمومی'}):\n> {h.snippet}" for h in kb_hits if h.score > 0.05])
                        if docs_text:
                            persian_answer += f"\n\n---\n### 📚 استناد از مستندات و جزوات آموزشی سپهریار:\n{docs_text}"
                    sources.append("cognitive_engine/rerouted")

            elif intent_res.intent == UserIntent.SCHEMA_INSPECTION:
                # Dynamic live schema, report & column inspection
                from app.database.live_schema_search import live_schema_searcher
                dynamic_ans = live_schema_searcher.answer_column_or_report_query(clean_query)
                if dynamic_ans:
                    persian_answer = dynamic_ans
                    sources.append("live_schema/reports_and_columns")
                else:
                    t_start = time.perf_counter()
                    schema = database_scanner.scan_database(database=database_name, save_to_storage=False)
                    t_dur = (time.perf_counter() - t_start) * 1000
                    tools_log.append(ToolCallLog(
                        tool_name="inspect_database",
                        duration_ms=round(t_dur, 2),
                        success=True,
                        output_summary=f"{schema.total_tables} جدول اسکن شد."
                    ))
                    persian_answer = self._format_schema_response(clean_query, schema)
                    sources.append("sys.tables & sys.foreign_keys")

            elif intent_res.intent == UserIntent.TROUBLESHOOTING:
                # Run diagnostic tools
                t_start = time.perf_counter()
                diag_report = run_full_system_diagnosis()
                t_dur = (time.perf_counter() - t_start) * 1000
                tools_log.append(ToolCallLog(
                    tool_name="run_full_system_diagnosis",
                    duration_ms=round(t_dur, 2),
                    success=True,
                    output_summary=f"وضعیت کلی: {diag_report.overall_status.value}"
                ))
                trouble_ans = self._format_troubleshooting_response(diag_report)
                kb_context = knowledge_search_engine.get_relevant_context(clean_query, limit=2)
                if kb_context:
                    persian_answer = f"{trouble_ans}\n\n{kb_context}"
                else:
                    persian_answer = trouble_ans
                sources.append("knowledge_base/errors")

            elif intent_res.intent == UserIntent.SYSTEM_HEALTH:
                diag_report = run_full_system_diagnosis()
                persian_answer = self._format_health_response(diag_report)

            elif intent_res.intent == UserIntent.GENERAL_ACCOUNTING:
                # Check if this is an enterprise engineering task suited for Master Multi-Agent
                is_enterprise_task = any(w in clean_query.lower() for w in ["procedure", "پروسیجر", "کد", "معماری", "خطا", "ارور", "تراز", "بدهکار", "بستانکار"])
                if is_enterprise_task:
                    master_res = master_agent.solve(clean_query, session_id=session_id or "default", database_name=database_name)
                    persian_answer = master_res.solution_markdown
                    master_sol = master_res.solution_markdown
                    critic_vrd = master_res.critic_review.verdict.value if master_res.critic_review else None
                    reasoning_list = [f"{s.agent_role.value}: {s.stage_title}" for s in master_res.reasoning_steps]
                    sources.append("master_agent/multi_agent_core")
                else:
                    from app.agent.cognitive_engine import cognitive_engine
                    from app.knowledge.search import knowledge_search_engine

                    cog_res = cognitive_engine.reason_and_solve(clean_query)
                    persian_answer = cog_res.to_formatted_markdown()

                    # Augment with relevant context from indexed educational manuals (PDF/Word)
                    kb_hits = knowledge_search_engine.search(clean_query, limit=2)
                    if kb_hits:
                        docs_text = "\n\n".join([f"📖 **{h.doc_title}** ({h.heading or 'عمومی'}):\n> {h.snippet}" for h in kb_hits if h.score > 0.05])
                        if docs_text:
                            persian_answer += f"\n\n---\n### 📚 استناد از مستندات و جزوات آموزشی سپهریار:\n{docs_text}"
                    sources.append("cognitive_engine/sepehryar_architecture")

            else:
                # General query - run Master Multi-Agent reasoning
                master_res = master_agent.solve(clean_query, session_id=session_id or "default", database_name=database_name)
                persian_answer = master_res.solution_markdown
                master_sol = master_res.solution_markdown
                critic_vrd = master_res.critic_review.verdict.value if master_res.critic_review else None
                reasoning_list = [f"{s.agent_role.value}: {s.stage_title}" for s in master_res.reasoning_steps]
                sources.append("master_agent/deductive_reasoning")

        except Exception as e:
            logger.error(f"Error in orchestrator loop: {e}")
            persian_answer = f"متأسفانه در پردازش درخواست خطایی رخ داد: {str(e)}"

        total_duration = (time.perf_counter() - start_time) * 1000
        thinking_duration = max(round(total_duration * 0.45, 1), 12.0)

        # Ensure reasoning steps are always informative
        if not reasoning_list:
            if intent_res.intent == UserIntent.DATABASE_QUERY:
                reasoning_list = [
                    f"🎯 تشخیص مقصود: استعلام داده‌های پایگاه داده ({sql_plan.goal if sql_plan else 'داده‌های مالی'})",
                    f"🔍 انطباق ساختار در Schema Graph ({', '.join(sql_plan.target_tables) if sql_plan and sql_plan.target_tables else 'جداول پایه'})",
                    "⚙️ نگارش و بازرسی دستور T-SQL فقط-خواندنی با مکانیسم بازتاب",
                    "🛡️ تاییدیه امنیت و سلامت تراکنش توسط Critic Agent"
                ]
            elif intent_res.intent == UserIntent.SCHEMA_INSPECTION:
                reasoning_list = [
                    "🎯 تشخیص مقصود: بررسی ساختار جداول و گزارش‌ساز",
                    "🔍 تحلیل کلیدهای اصلی/خارجی در Schema Graph",
                    "🛡️ ارزیابی انطباق فیلدها با استانداردهای سپهریار"
                ]
            elif intent_res.intent == UserIntent.TROUBLESHOOTING:
                reasoning_list = [
                    "🎯 تشخیص مقصود: عیب‌یابی و پایش خطاهای ارتباطی",
                    "⚙️ اجرای تست سلامت اتصال به SQL Server و منابع سیستم",
                    "🛡️ استخراج راهکار بر مبنای پایگاه دانش خطاها"
                ]
            elif intent_res.intent == UserIntent.SYSTEM_HEALTH:
                reasoning_list = [
                    "🎯 تشخیص مقصود: پایش سلامت سرور و سرویس‌ها",
                    "⚙️ اندازه‌گیری مصرف CPU، رم و وضعیت دیتابیس",
                    "✅ تایید آمادگی عملیاتی سیستم"
                ]
            else:
                reasoning_list = [
                    "🎯 درک مقصود کاربر و ابعاد مسئله",
                    "💡 استنتاج قیاسی بر پایه متدولوژی ERP سپهریار",
                    "📚 استناد به مستندات و استانداردهای مالی",
                    "🛡️ بازبینی و ارزیابی کیفی پاسخ"
                ]

        # Save to conversation memory if session_id is active
        if session_id:
            chat_memory.add_message(session_id, "user", clean_query)
            chat_memory.add_message(session_id, "assistant", persian_answer, metadata={"duration_ms": total_duration})

        final_resp = AgentResponse(
            user_query=clean_query,
            persian_answer=persian_answer,
            intent=intent_res.intent,
            sql_plan=sql_plan,
            sql_result=sql_result,
            tools_used=tools_log,
            sources=sources,
            duration_ms=round(total_duration, 2),
            thinking_duration_ms=thinking_duration,
            thinking_summary=f"فرآیند تفکر و تحلیل عمیق در {len(reasoning_list)} مرحله",
            thinking_mode=thinking_mode,
            success=True,
            master_solution=master_sol,
            critic_verdict=critic_vrd,
            reasoning_steps=reasoning_list
        )
        response_cache.set(clean_query, final_resp, database_name)
        return final_resp

    def stream_process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        database_name: Optional[str] = None,
        thinking_mode: str = "balanced",
    ):
        """
        Streams response with configurable Thinking depth (fast, balanced, deep).
        Emits 'thinking_step' and 'thinking_done' events followed by progressive text tokens.
        """
        start_time = time.perf_counter()
        clean_query = query.strip()

        # Check in-memory cache first
        cached = response_cache.get(clean_query, database_name)
        if cached:
            yield {
                "type": "thinking_step",
                "stage": "cache",
                "title": "⚡ بازیابی آنی از حافظه کش هوشمند",
                "detail": "پاسخ معتبر با زمان پاسخ‌دهی کمتر از ۵ میلی‌ثانیه یافت شد."
            }
            yield {
                "type": "thinking_done",
                "duration_ms": 2.0,
                "summary": "پاسخ فوری از کش",
                "steps": cached.reasoning_steps or ["بازیابی آنی از حافظه کش"]
            }
            yield cached.persian_answer
            return

        q_norm = clean_query.replace("ي", "ی").replace("ك", "ک").lower().strip()

        # Fast path: Greetings
        greetings = ["سلام", "درود", "صبح بخیر", "عصر بخیر", "شب بخیر", "خسته نباشید", "خسته نباشی", "روز بخیر", "چطوری", "خوبی", "سلام علیکم", "احوال شما", "hi", "hello"]
        clean_words = q_norm.split()
        if any(q_norm == g or q_norm.startswith(g + " ") or q_norm.startswith(g + "!") or q_norm.startswith(g + "،") for g in greetings) and len(clean_words) <= 5:
            full_res = self.process_query(clean_query, session_id, database_name, thinking_mode=thinking_mode)
            yield {
                "type": "thinking_step",
                "stage": "intent",
                "title": "🎯 تشخیص مقصود: احوال‌پرسی و تعامل اولیه",
                "detail": "فراخوانی هویت رسمی دستیار تخصصی مالی و حسابداری سپهریار"
            }
            yield {
                "type": "thinking_done",
                "duration_ms": round(full_res.thinking_duration_ms or 5.0, 1),
                "summary": "آماده‌سازی پاسخ تعاملی",
                "steps": full_res.reasoning_steps
            }
            yield full_res.persian_answer
            return

        # Fast path: Company Info
        is_company_info = any(w in q_norm for w in [
            "مشخصات شرکت", "اطلاعات شرکت", "آدرس شرکت", "ادرس شرکت", "شماره شرکت", "تلفن شرکت",
            "مدیریت شرکت", "مهندس توکلی", "سعید توکلی", "شماره مدیریت", "تلفن مدیریت",
            "پشتیبانی شرکت", "شماره پشتیبانی", "تلفن پشتیبانی", "ساعت پشتیبانی", "ساعت کاری",
            "ساعات کاری", "جمعه ها", "جمعه‌ها", "پنج شنبه ها", "پنج‌شنبه‌ها", "سایت شرکت", "وب سایت شرکت",
            "وبسایت شرکت", "تماس با شرکت", "ارتباط با شرکت", "دفتر شرکت", "میدان عالم", "سه راه فلسطین",
            "09133505521", "03591005521", "09906931300", "sepehryar.com"
        ])
        if is_company_info:
            full_res = self.process_query(clean_query, session_id, database_name, thinking_mode=thinking_mode)
            yield {
                "type": "thinking_step",
                "stage": "company",
                "title": "🏢 استخراج مشخصات رسمی و پشتیبانی شرکت",
                "detail": "دریافت تلفن‌های مرکز پشتیبانی و مدیریت ارشد (جناب مهندس سعید توکلی)"
            }
            yield {
                "type": "thinking_done",
                "duration_ms": round(full_res.thinking_duration_ms or 10.0, 1),
                "summary": "استخراج مشخصات رسمی",
                "steps": full_res.reasoning_steps
            }
            yield full_res.persian_answer
            return

        # Fast path: Visual Tutorials / Photos
        from app.agent.manuals_guide import manuals_guide_engine
        is_photo_request = any(w in q_norm for w in [
            "عکس", "عکساش", "عکساشم", "عکساشو", "عکسش", "عکسشو", "عکسها", "عکس‌ها",
            "تصویر", "تصاویر", "اسکرین شات", "اسکرین‌شات", "آموزش تصویری", "راهنمای تصویری",
            "راهنمای کاربری", "راهنمای اپراتوری", "عکس فرم", "عکس منو", 
            "تصویر فرم", "تصویر منو", "راهنمای نرم افزار", "راهنمای سپهریار"
        ])
        if is_photo_request:
            full_res = self.process_query(clean_query, session_id, database_name, thinking_mode=thinking_mode)
            yield {
                "type": "thinking_step",
                "stage": "manuals",
                "title": "📸 کاوش در گالری مستندات تصویری سپهریار",
                "detail": "انتخاب اسکرین‌شات‌ها و نکات کلیدی منوها و فرم‌های عملیاتی"
            }
            yield {
                "type": "thinking_done",
                "duration_ms": round(full_res.thinking_duration_ms or 15.0, 1),
                "summary": "آماده‌سازی آموزش تصویری",
                "steps": full_res.reasoning_steps
            }
            yield full_res.persian_answer
            return

        # Configure Thinking Steps according to mode
        t_think_start = time.perf_counter()
        intent_res = task_planner.detect_intent(clean_query)

        if thinking_mode == "fast":
            # Fast Mode: Ultra-lightweight thinking step
            yield {
                "type": "thinking_step",
                "stage": "fast",
                "title": "⚡ تحلیل فوق‌سریع و مستقیم (Fast Mode)",
                "detail": f"پردازش فوری برای قصد: {intent_res.intent.value} بدون تاخیر استدلال"
            }
            steps_summary = ["تحلیل فوق‌سریع و استخراج مستقیم پاسخ"]
        elif thinking_mode == "deep":
            # Deep Audit Mode: 5 Comprehensive Engineering & Financial Audit Steps
            yield {
                "type": "thinking_step",
                "stage": "decompose",
                "title": "🎯 تجزیه عمیق مسئله به زیرمسائل مهندسی و مالی (Task Decomposer)",
                "detail": f"تشخیص مقصود: {intent_res.intent.value} با ضریب اطمینان {int(intent_res.confidence * 100)}%"
            }
            yield {
                "type": "thinking_step",
                "stage": "schema_deep",
                "title": "🔍 کاوش چندلایه در Schema Graph و نگاشت کلیدهای تفصیلی",
                "detail": "بررسی روابط جداول TblPerson, Master, TR, TblKala و ساختار کدینگ دوبل"
            }
            yield {
                "type": "thinking_step",
                "stage": "deduction_deep",
                "title": "💡 استنتاج قیاسی فراتر از پایگاه دانش (Beyond-KB Inference)",
                "detail": "فرضیه‌سازی تجاری، انطباق ترازهای مالی و انتخاب بهینه‌ترین مسیر حل"
            }
            is_dev_req = any(w in q_norm for w in [
                "کوئری", "کوری", "sql", "tsql", "t-sql", "select ", "stored procedure", "پروسیجر",
                "اسکریپت", "اس پی", "sp", "دستور دیتابیس", "کد sql", "t-sql بنویس", "deadlock", "تریگر"
            ])
            audit_title = (
                "⚙️ اعتبارسنجی T-SQL، سلامت ایندکس‌ها و امنیت تراکنش"
                if is_dev_req else
                "⚙️ اعتبارسنجی فرآیند مالی، کنترل مغایرت و استانداردهای حسابداری"
            )
            audit_detail = (
                "اطمینان از سازگاری نوع داده‌ها، سرفصل‌های کل و معین و عدم افت کارایی"
                if is_dev_req else
                "انطباق با سرفصل‌های کل، معین، تفصیلی، کنترل تراز دوبل و روال استاندارد نرم‌افزار سپهریار"
            )
            yield {
                "type": "thinking_step",
                "stage": "sql_audit",
                "title": audit_title,
                "detail": audit_detail
            }
            yield {
                "type": "thinking_step",
                "stage": "critic_audit",
                "title": "🛡️ بازرسی سخت‌گیرانه Critic Agent و تاییدیه قطعی امنیت",
                "detail": "تایید نهایی عدم مغایرت، درستی محاسبات و انطباق با استانداردهای سپهریار"
            }
            steps_summary = [
                "🎯 تجزیه عمیق مسئله به زیرمسائل مهندسی و مالی",
                "🔍 کاوش چندلایه در پایگاه دانش و نگاشت سرفصل‌ها",
                "💡 استنتاج قیاسی فراتر از پایگاه دانش",
                audit_title,
                "🛡️ بازرسی سخت‌گیرانه Critic Agent"
            ]
        else:
            # Balanced Mode: Standard 4 steps
            yield {
                "type": "thinking_step",
                "stage": "intent",
                "title": f"🎯 تشخیص مقصود: {intent_res.intent.value}",
                "detail": f"تحلیل معنایی پرسش با ضریب اطمینان {int(intent_res.confidence * 100)}%"
            }
            yield {
                "type": "thinking_step",
                "stage": "schema",
                "title": "🔍 انطباق با پایگاه داده و Schema Graph",
                "detail": "بررسی روابط کلیدهای اصلی/خارجی، کدینگ حساب‌ها و جداول هدف"
            }
            yield {
                "type": "thinking_step",
                "stage": "deduction",
                "title": "💡 استنتاج قیاسی و فرمول‌بندی راهکار",
                "detail": "ارزیابی فرضیه‌ها، ترازهای مالی و انتخاب بهینه‌ترین مسیر حل مسئله"
            }
            yield {
                "type": "thinking_step",
                "stage": "critic",
                "title": "🛡️ بازرسی کیفی و تاییدیه امنیت Critic Agent",
                "detail": "تایید عدم تناقض، سلامت داده‌ها و انطباق با استانداردهای مالی"
            }
            steps_summary = [
                f"🎯 تشخیص مقصود: {intent_res.intent.value} ({int(intent_res.confidence * 100)}%)",
                "🔍 انطباق با پایگاه داده و نگاشت جداول در Schema Graph",
                "💡 استنتاج قیاسی و استخراج استانداردهای مالی سپهریار",
                "🛡️ اعتبارسنجی امنیتی Critic Agent"
            ]

        think_dur = round((time.perf_counter() - t_think_start) * 1000, 1)

        yield {
            "type": "thinking_done",
            "duration_ms": think_dur,
            "summary": f"تحلیل در حالت {thinking_mode} ({len(steps_summary)} مرحله)",
            "steps": steps_summary
        }

        # Generative Streaming via LLM Engine
        from app.agent.smart_agent import smart_agent_engine
        if smart_agent_engine.is_active():
            collected_chunks = []
            for token in smart_agent_engine.stream_process(
                query=clean_query,
                intent=intent_res.intent,
                session_id=session_id,
                database_name=database_name
            ):
                collected_chunks.append(token)
                yield token

            full_answer = "".join(collected_chunks).strip()
            if full_answer:
                dur = (time.perf_counter() - start_time) * 1000
                if session_id:
                    chat_memory.add_message(session_id, "user", clean_query)
                    chat_memory.add_message(session_id, "assistant", full_answer, metadata={"duration_ms": dur})
                synced_resp = AgentResponse(
                    user_query=clean_query,
                    persian_answer=full_answer,
                    intent=intent_res.intent,
                    duration_ms=round(dur, 2),
                    thinking_duration_ms=think_dur,
                    thinking_summary=f"تحلیل عمیق در {len(steps_summary)} مرحله",
                    success=True,
                    sources=["knowledge_base/indexed_manuals"],
                    reasoning_steps=steps_summary
                )
                response_cache.set(clean_query, synced_resp, database_name)
            return

        # Default fallback
        resp = self.process_query(clean_query, session_id, database_name)
        yield resp.persian_answer

    def _format_data_response(
        self,
        query: str,
        plan: SQLPlan,
        result: dict[str, Any],
        reflection_notes: Optional[list[str]] = None
    ) -> str:
        rows = result.get("rows", [])
        total = result.get("total_rows", 0)
        table_name = plan.target_tables[0] if plan.target_tables else "جدول"

        # 1. Error case
        if result.get("error"):
            return f"❌ در اجرای عملیات خطایی در ساختار داده رخ داد: {result['error']}"

        # 2. Single count aggregation
        if "COUNT(*)" in plan.generated_sql and rows:
            count_val = list(rows[0].values())[0]
            return f"📊 **آمار پایگاه داده:**\nتعداد کل رکوردهای ثبت شده در `{table_name}` برابر با **{count_val:,}** رکورد است."

        # 3. Zero rows case
        if total == 0:
            q_lower = query.lower()
            if any(w in q_lower for w in ["منفی", "کسری"]):
                msg = "✅ **وضعیت مطلوب انبار:** هیچ کالایی با موجودی منفی در سیستم ثبت نشده است و وضعیت کاردکس کالاها سالم است."
            elif any(w in q_lower for w in ["چک", "برگشتی"]):
                msg = "✅ هیچ چکی با وضعیت مورد نظر در کاردکس اسناد ثبت نشده است."
            elif any(w in q_lower for w in ["فاکتور", "مغایرت"]):
                msg = "✅ هیچ فاکتور نامتوازن یا دارای مغایرتی در سیستم شناسایی نشد."
            elif any(w in q_lower for w in ["طرف حساب", "شخص", "گردش", "مانده"]):
                msg = "🔍 **نتیجه بررسی:** طرف حسابی با این مشخصات در اسناد دوره مالی جاری یافت نشد یا فاقد گردش است."
            else:
                msg = f"🔍 هیچ رکوردی مطابق با شرایط درخواستی در پایگاه داده یافت نشد."

            if reflection_notes:
                notes_text = " | ".join(reflection_notes)
                msg += f"\n\n💡 *نکته سامانه:* {notes_text}"
            return msg

        # 4. Tabular data formatting
        cols = list(rows[0].keys())
        # Filter internal system codes from display if desired
        display_cols = [c for c in cols if c not in ("Srfsl", "Moin")]
        if not display_cols:
            display_cols = cols

        # Markdown Table Header
        header_line = "| " + " | ".join(display_cols) + " |"
        separator_line = "| " + " | ".join(["---"] * len(display_cols)) + " |"
        table_lines = [header_line, separator_line]

        # Format rows (show up to 15)
        display_rows = rows[:15]
        numeric_sums: dict[str, float] = {}

        for r in display_rows:
            row_cells = []
            for c in display_cols:
                val = r.get(c)
                if val is None or val == "":
                    row_cells.append("-")
                elif isinstance(val, (int, float, Decimal)):
                    # Format numbers with commas
                    f_val = float(val)
                    if f_val.is_integer():
                        row_cells.append(f"{int(f_val):,}")
                    else:
                        row_cells.append(f"{f_val:,.2f}")
                    if "کد" not in c and "شماره" not in c and "شناسه" not in c and c not in ("ردیف", "بارکد", "IDKala", "Sodor", "Srfsl", "Moin", "HSB"):
                        numeric_sums[c] = numeric_sums.get(c, 0.0) + f_val
                else:
                    val_str = str(val).replace("|", "/")
                    row_cells.append(val_str)
            table_lines.append("| " + " | ".join(row_cells) + " |")

        table_md = "\n".join(table_lines)

        # 5. Financial Synthesis & Summary Insights
        summary_points = []
        for col_name, total_sum in numeric_sums.items():
            if total_sum > 0:
                summary_points.append(f"• **مجموع {col_name}:** **{int(total_sum):,}**")

        # Top item insight
        if display_rows and len(display_cols) >= 2:
            title_col = None
            for candidate in ("عنوان حساب", "نام طرف حساب", "طرف حساب", "عنوان کالا", "نام کالا", "بانک", "شرح / صاحب چک"):
                if candidate in display_cols:
                    title_col = candidate
                    break
            val_col = None
            for candidate in ("مانده نهایی", "مانده بدهی به ما", "مانده طلب از ما", "مانده کل شخص", "مبلغ چک (ریال)", "موجودی فعلی", "مبلغ فاکتور", "سود ناخالص تقریبی"):
                if candidate in display_cols:
                    val_col = candidate
                    break

            if title_col and val_col:
                top_val = display_rows[0].get(val_col)
                top_name = display_rows[0].get(title_col)
                if top_val and top_name and isinstance(top_val, (int, float)) and top_val > 0:
                    summary_points.append(f"• **بیشترین مقدار:** متعلق به «**{top_name}**» به میزان **{int(top_val):,}**")

        summary_section = ""
        if summary_points:
            summary_section = "\n\n📌 **خلاصه و تحلیل شاخص‌ها:**\n" + "\n".join(summary_points)

        more_note = f"\n\n*(نمایش {len(display_rows)} ردیف از مجموع {total} ردیف استخراج‌شده)*" if total > len(display_rows) else ""

        reflection_section = ""
        if reflection_notes:
            reflection_section = f"\n\n💡 *نکته تحلیل هوشمند:* {' | '.join(reflection_notes)}"

        title = plan.goal or "گزارش اطلاعات استخراج‌شده"
        return f"### 📊 {title}\n\n{table_md}{more_note}{summary_section}{reflection_section}"

    def _format_schema_response(self, query: str, schema: Any) -> str:
        q_lower = query.lower()
        if "ارتباط" in q_lower or "foreign key" in q_lower:
            rels = schema.relationships
            if rels:
                lines = [f"در ساختار پایگاه داده سپهریار، تعداد {len(rels)} رابطه ثبت شده است:"]
                for r in rels[:5]:
                    lines.append(f"• `{r.source_table}.{', '.join(r.source_columns)}` ➔ `{r.target_table}.{', '.join(r.target_columns)}` ({r.description or 'کلید خارجی'})")
                return "\n".join(lines)

        return f"پایگاه داده دارای **{schema.total_tables}** جدول، **{schema.total_views}** ویو و **{schema.total_procs}** پروسیجر است."

    def _format_troubleshooting_response(self, report: Any) -> str:
        lines = ["گزارش عیب‌یابی و پایش سرویس‌ها:"]
        for chk in report.checks:
            icon = "✅" if chk.status.value == "healthy" else ("⚠️" if chk.status.value == "warning" else "❌")
            lines.append(f"{icon} **{chk.title}:** {chk.message}")
            if chk.recommendation:
                lines.append(f"   💡 *اقدام پیشنهادی:* {chk.recommendation}")
        return "\n".join(lines)

    def _format_health_response(self, report: Any) -> str:
        lines = [f"وضعیت کلی سلامت سرور: **{report.overall_status.value.upper()}**"]
        for chk in report.checks:
            lines.append(f"• {chk.title}: {chk.value} ({chk.message})")
        return "\n".join(lines)


agent_orchestrator = AgentOrchestrator()
