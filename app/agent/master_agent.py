"""
Master Agent: The central AI Software Engineer Orchestrator & Reasoning Coordinator for Sepehryar ERP.
Understands intent, decomposes problems, coordinates specialized agents, fosters abductive inference,
synthesizes cross-agent solutions, and enforces strict Critic quality verification.
"""
import time
from typing import Optional, Any
from pydantic import BaseModel, Field

from app.agent.specialized.base import (
    AgentRole,
    CriticVerdict,
    AgentTask,
    AgentResult,
    CriticReview,
    Blackboard,
    ReasoningStep,
)
from app.agent.specialized.database_agent import DatabaseAgent
from app.agent.specialized.sql_agent import SQLAgent
from app.agent.specialized.procedure_agent import ProcedureAgent
from app.agent.specialized.code_agent import CodeAgent
from app.agent.specialized.debug_agent import DebugAgent
from app.agent.specialized.architecture_agent import ArchitectureAgent
from app.agent.specialized.critic_agent import CriticAgent
from app.agent.reasoning.deductive_engine import deductive_engine
from app.agent.reasoning.task_decomposer import task_decomposer
from app.core.logger import get_logger

logger = get_logger("agent.master_agent")


class MasterAgentResponse(BaseModel):
    query: str
    solution_markdown: str
    critic_review: Optional[CriticReview] = None
    sub_agent_results: dict[str, AgentResult] = Field(default_factory=dict)
    reasoning_steps: list[ReasoningStep] = Field(default_factory=list)
    generated_sql: Optional[str] = None
    generated_sp: Optional[str] = None
    generated_code: Optional[str] = None
    total_duration_ms: float = 0.0
    success: bool = True


class MasterAgent:
    """
    Master AI Software Engineer for Sepehryar ERP:
    Coordinates all 7 specialized agents, reasons beyond the knowledge base,
    and guarantees high-quality, safe engineering solutions.
    """

    def __init__(self):
        self.database_agent = DatabaseAgent()
        self.sql_agent = SQLAgent()
        self.procedure_agent = ProcedureAgent()
        self.code_agent = CodeAgent()
        self.debug_agent = DebugAgent()
        self.architecture_agent = ArchitectureAgent()
        self.critic_agent = CriticAgent()

        self._agent_registry = {
            AgentRole.DATABASE: self.database_agent,
            AgentRole.SQL: self.sql_agent,
            AgentRole.PROCEDURE: self.procedure_agent,
            AgentRole.CODE: self.code_agent,
            AgentRole.DEBUG: self.debug_agent,
            AgentRole.ARCHITECTURE: self.architecture_agent,
            AgentRole.CRITIC: self.critic_agent,
        }

    def solve(
        self,
        query: str,
        session_id: str = "default",
        database_name: Optional[str] = None
    ) -> MasterAgentResponse:
        start_time = time.perf_counter()
        logger.info(f"Master Agent initiating coordination for query: '{query}'")

        # 1. Initialize Blackboard
        blackboard = Blackboard(
            session_id=session_id,
            user_query=query,
            database_name=database_name,
        )
        blackboard.add_step(
            AgentRole.MASTER,
            "تحلیل اولیه و فهم مسئله",
            f"درک درخواست کاربر و ارزیابی ابعاد مسئله: '{query}'"
        )

        # 2. Beyond-KB Deductive Reasoning & Hypotheses
        deductive_engine.perform_deductive_reasoning(query, blackboard)

        # 3. Task Decomposition into specialized subtasks
        tasks = task_decomposer.decompose(query, session_id=session_id)
        blackboard.add_step(
            AgentRole.MASTER,
            "تقسیم وظایف بین ایجنت‌های تخصصی",
            f"برنامه‌ریزی {len(tasks)} گام تخصصی شامل: {', '.join(t.role.value for t in tasks)}"
        )

        # 4. Sequential Execution & Inter-Agent Coordination
        for task in tasks:
            agent = self._agent_registry.get(task.role)
            if agent:
                try:
                    logger.debug(f"Invoking {agent.role.value} agent for task {task.task_id}...")
                    agent.execute(task, blackboard)
                except Exception as ex:
                    logger.error(f"Error in {agent.role.value} execution: {ex}", exc_info=True)
                    blackboard.add_step(
                        task.role,
                        f"خطا در اجرای ایجنت {agent.role.value}",
                        f"استثنا: {str(ex)}"
                    )

        # 5. Critic Verification Review
        critic_res = blackboard.critic_reviews[-1] if blackboard.critic_reviews else self.critic_agent.review_solution(blackboard)

        # 6. Self-Correction Loop (if Critic rejected)
        if critic_res.verdict == CriticVerdict.REJECTED:
            blackboard.add_step(
                AgentRole.MASTER,
                "حلقه اصلاح خودکار (Self-Correction)",
                f"ایجنت Critic راه‌حل را ریجکت کرد: {'; '.join(critic_res.concerns_or_critiques)}. آغاز اصلاح تراکنش و اسکریپت."
            )
            # Re-run SQL agent with explicit correction context
            correction_task = AgentTask(
                task_id="correction_sql",
                role=AgentRole.SQL,
                goal=f"اصلاح کوئری با رعایت الزامات Critic: {query}",
                priority=90
            )
            self.sql_agent.execute(correction_task, blackboard)
            # Re-evaluate
            critic_res = self.critic_agent.review_solution(blackboard)

        # 7. Synthesize Unified Persian Engineering Solution
        solution_md = self._synthesize_solution(blackboard, critic_res)
        blackboard.final_solution = solution_md

        duration = (time.perf_counter() - start_time) * 1000

        return MasterAgentResponse(
            query=query,
            solution_markdown=solution_md,
            critic_review=critic_res,
            sub_agent_results=blackboard.agent_results,
            reasoning_steps=blackboard.reasoning_chain,
            generated_sql=blackboard.generated_sql,
            generated_sp=blackboard.generated_sp,
            generated_code=blackboard.generated_code,
            total_duration_ms=round(duration, 2),
            success=(critic_res.verdict != CriticVerdict.REJECTED)
        )

    def _synthesize_solution(self, blackboard: Blackboard, critic: CriticReview) -> str:
        """Synthesizes rich, multi-perspective Persian engineering report."""
        sections = []

        # Header
        sections.append(f"## 🧠 راهکار مهندسی Sepehryar AI Core\n")

        # Hypotheses & Beyond-KB Deduction
        if blackboard.active_hypotheses:
            sections.append("### ۱. استدلال و فرضیه‌های مهندسی (Beyond-KB Inference):")
            for h in blackboard.active_hypotheses:
                sections.append(f"- **{h.statement}** (ضریب اطمینان: {int(h.confidence * 100)}%)\n  > 💡 مبنای ساختاری: {h.basis}")
            sections.append("")

        # Findings of specialized agents
        sections.append("### ۲. تحلیل تخصصی ایجنت‌های همکار:")
        for role, res in blackboard.agent_results.items():
            if role == AgentRole.CRITIC.value:
                continue
            sections.append(f"#### 🔹 {res.summary}")
            for f in res.findings[:4]:
                sections.append(f"- {f}")
            if res.warnings:
                for w in res.warnings:
                    sections.append(f"- ⚠️ {w}")
            sections.append("")

        # Generated Artifacts (SP, SQL, C# Code) - Only if explicitly requested
        is_code_requested = any(w in blackboard.user_query.lower() for w in [
            "کوئری", "کوری", "sql", "tsql", "t-sql", "select ", "stored procedure", "پروسیجر",
            "اسکریپت", "اس پی", "sp", "دستور دیتابیس", "کد sql", "t-sql بنویس", "c#", ".net"
        ])

        if is_code_requested:
            if blackboard.generated_sp:
                sections.append("### ۳. اسکریپت Stored Procedure سازمانی سپهریار:")
                sections.append(f"```sql\n{blackboard.generated_sp.strip()}\n```\n")

            if blackboard.generated_sql and not blackboard.generated_sp:
                sections.append("### ۳. اسکریپت بهینه‌شده T-SQL:")
                sections.append(f"```sql\n{blackboard.generated_sql.strip()}\n```\n")

            if blackboard.generated_code:
                sections.append("### ۴. پیاده‌سازی لایه کد و اتصال نرم‌افزار (C# / .NET):")
                sections.append(f"```csharp\n{blackboard.generated_code.strip()}\n```\n")

        # Critic Gatekeeper Stamp
        verdict_icon = "✅" if critic.verdict == CriticVerdict.APPROVED else ("⚠️" if critic.verdict == CriticVerdict.APPROVED_WITH_WARNINGS else "❌")
        sections.append(f"### ۵. گواهی ارزیابی کیفی Critic Agent ({verdict_icon} وضعیت: {critic.verdict.value.upper()}):")
        for sc in critic.safety_checks:
            sections.append(f"- [x] {sc}")
        if critic.concerns_or_critiques:
            sections.append("\n**ملاحظات Critic:**")
            for c in critic.concerns_or_critiques:
                sections.append(f"- ⚠️ {c}")
        if critic.recommendations:
            sections.append("\n**توصیه‌های اجرایی:**")
            for r in critic.recommendations:
                sections.append(f"- 💡 {r}")

        return "\n".join(sections)


master_agent = MasterAgent()
