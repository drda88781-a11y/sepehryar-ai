"""
Central Agent Orchestrator: executes the reasoning cycle:
Understand -> Plan -> Retrieve -> Tool Call -> Validate -> Analyze -> Respond.
"""
import time
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

logger = get_logger("orchestrator")


class AgentOrchestrator:
    """Orchestrates natural language understanding, database tools, and Persian response generation."""

    def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        database_name: Optional[str] = None,
    ) -> AgentResponse:
        """Run the complete agent cognitive loop."""
        start_time = time.perf_counter()
        clean_query = query.strip()
        logger.info(f"Agent processing query: '{clean_query}'...")

        tools_log: list[ToolCallLog] = []
        sql_plan: Optional[SQLPlan] = None
        sql_result: Optional[dict[str, Any]] = None
        sources: list[str] = []

        # 1. Understand: Detect Intent
        intent_res = task_planner.detect_intent(clean_query)
        logger.debug(f"Detected intent: {intent_res.intent.value} (confidence={intent_res.confidence})")

        persian_answer = ""

        # 2. Plan & Tool Execution based on Intent
        try:
            if intent_res.intent == UserIntent.DATABASE_QUERY:
                # Load active schema to guide column and join resolution
                target_db = database_name or settings.sql_database
                active_schema = storage_repo.get_database_metadata(target_db)

                # Formulate SQL Plan
                sql_plan = task_planner.generate_sql_plan(clean_query, active_schema=active_schema)
                if sql_plan and sql_plan.validation_status:
                    # Execute safe query
                    t_start = time.perf_counter()
                    sql_result = safe_sql_executor.execute_readonly_query(
                        sql=sql_plan.generated_sql,
                        database=database_name,
                        max_rows=sql_plan.row_limit,
                        mask_sensitive=True
                    )
                    t_dur = (time.perf_counter() - t_start) * 1000
                    tools_log.append(ToolCallLog(
                        tool_name="run_safe_select",
                        arguments={"sql": sql_plan.generated_sql},
                        duration_ms=round(t_dur, 2),
                        success=True,
                        output_summary=f"{sql_result['total_rows']} ردیف داده دریافت شد."
                    ))

                    # Synthesize Persian response
                    persian_answer = self._format_data_response(clean_query, sql_plan, sql_result)
                else:
                    persian_answer = "کوئری استخراج داده برای این پرسش شرایط امنیتی را احراز نکرد."

            elif intent_res.intent == UserIntent.SCHEMA_INSPECTION:
                # Inspect schema or relationships
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
                # Search offline knowledge base
                kb_context = knowledge_search_engine.get_relevant_context(clean_query, limit=3)
                if kb_context:
                    persian_answer = (
                        f"بر اساس مستندات و استانداردهای پایگاه دانش سپهریار:\n\n"
                        f"{kb_context}\n\n"
                        f"💡 در صورت نیاز به بررسی دقیق‌تر کدینگ یا جداول مربوطه، سوال خود را مطرح فرمایید."
                    )
                    sources.append("knowledge_base/database")
                else:
                    llm_res = llm_manager.generate(clean_query)
                    persian_answer = llm_res.content

            else:
                # General LLM answer with KB fallback
                kb_context = knowledge_search_engine.get_relevant_context(clean_query, limit=2)
                if kb_context:
                    persian_answer = f"{kb_context}"
                    sources.append("knowledge_base")
                else:
                    llm_res = llm_manager.generate(clean_query)
                    persian_answer = llm_res.content

        except Exception as e:
            logger.error(f"Error in orchestrator loop: {e}")
            persian_answer = f"متأسفانه در پردازش درخواست خطایی رخ داد: {str(e)}"

        total_duration = (time.perf_counter() - start_time) * 1000

        # Save to conversation memory if session_id is active
        if session_id:
            chat_memory.add_message(session_id, "user", clean_query)
            chat_memory.add_message(session_id, "assistant", persian_answer, metadata={"duration_ms": total_duration})

        return AgentResponse(
            user_query=clean_query,
            persian_answer=persian_answer,
            intent=intent_res.intent,
            sql_plan=sql_plan,
            sql_result=sql_result,
            tools_used=tools_log,
            sources=sources,
            duration_ms=round(total_duration, 2),
            success=True
        )

    def _format_data_response(self, query: str, plan: SQLPlan, result: dict[str, Any]) -> str:
        rows = result.get("rows", [])
        total = result.get("total_rows", 0)

        # Single count aggregation
        if "COUNT(*)" in plan.generated_sql and rows:
            count_val = list(rows[0].values())[0]
            table_name = plan.target_tables[0] if plan.target_tables else "جدول"
            return f"تعداد کل رکوردهای ثبت شده در {table_name} برابر با **{count_val:,}** رکورد است."

        # Tabular data summary
        table_name = plan.target_tables[0] if plan.target_tables else "جدول"
        return f"برای پاسخ به پرسش شما، جدول `{table_name}` با موفقیت بررسی شد و تعداد **{total}** ردیف اطلاعات با رعایت سقف امنیتی استخراج گردید."

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
