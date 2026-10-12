"""
Task Decomposer for Sepehryar AI Master Agent:
Breaks down high-level user requests into a coordinated sequence of specialized agent tasks.
"""
from typing import Optional
from app.agent.specialized.base import AgentTask, AgentRole, Blackboard
from app.core.logger import get_logger

logger = get_logger("agent.reasoning.decomposer")


class TaskDecomposer:
    """
    Analyzes user intent and generates a directed task workflow for the specialized agents.
    """

    def decompose(self, query: str, session_id: str = "default") -> list[AgentTask]:
        clean_q = query.lower()
        tasks: list[AgentTask] = []

        is_procedure = any(w in clean_q for w in ["procedure", "پروسیجر", "اس پی", "sp"])
        is_debug = any(w in clean_q for w in ["خطا", "ارور", "مشکل", "error", "exception", "باگ", "deadlock", "شکست"])
        is_code = any(w in clean_q for w in ["کد", "برنامه", "c#", ".net", "کلاس", "سرویس", "method"])
        is_architecture = any(w in clean_q for w in ["معماری", "ماژول", "اثر", "ریسک", "impact", "architecture"])
        is_sql = any(w in clean_q for w in ["کوئری", "کوری", "select", "sql", "اسکریپت", "گزارش", "مانده", "گردش"])

        task_idx = 1

        if is_procedure:
            # 1. Database Agent: Discover schema, keys, triggers
            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.DATABASE,
                goal=f"کشف ساختار جداول، کلیدها و تریگرهای مرتبط با: {query}",
                priority=1
            ))
            task_idx += 1

            # 2. Architecture Agent: Impact analysis & no-touch areas
            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.ARCHITECTURE,
                goal=f"تحلیل جایگاه ماژولار و مناطق غیرقابل تغییر برای: {query}",
                priority=2
            ))
            task_idx += 1

            # 3. Procedure Agent: Engineer enterprise SP
            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.PROCEDURE,
                goal=query,
                priority=3
            ))
            task_idx += 1

            # 4. Code Agent: Generate C# caller
            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.CODE,
                goal=f"پیاده‌سازی متد فراخوان در C# برای پروسیجر مرتبط با: {query}",
                priority=4
            ))
            task_idx += 1

        elif is_debug:
            # 1. Debug Agent: Root Cause Analysis
            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.DEBUG,
                goal=query,
                priority=1
            ))
            task_idx += 1

            # 2. Database Agent: Check involved tables and constraints
            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.DATABASE,
                goal=f"بررسی قیدها، ایندکس‌ها و وضعیت جداول درگیر خطا برای: {query}",
                priority=2
            ))
            task_idx += 1

            # 3. SQL Agent: Generate diagnostic or remedial SQL
            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.SQL,
                goal=f"طراحی کوئری تشخیصی و اصلاحی جهت رفع خطای: {query}",
                priority=3
            ))
            task_idx += 1

        elif is_code:
            # 1. Database Agent: Discover entities
            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.DATABASE,
                goal=f"استخراج نگاشت موجودیت‌های دیتابیس برای لایه کد: {query}",
                priority=1
            ))
            task_idx += 1

            # 2. Code Agent: Generate architectural C# / .NET code
            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.CODE,
                goal=query,
                priority=2
            ))
            task_idx += 1

        elif is_architecture:
            # 1. Architecture Agent
            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.ARCHITECTURE,
                goal=query,
                priority=1
            ))
            task_idx += 1

            # 2. Database Agent: Graph dependencies
            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.DATABASE,
                goal=f"استخراج گراف وابستگی‌های دیتابیس برای تحلیل معماری: {query}",
                priority=2
            ))
            task_idx += 1

        else:
            # Standard Intelligent DB & SQL Engineering Pipeline
            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.DATABASE,
                goal=f"کشف جداول، کلیدها و روابط برای: {query}",
                priority=1
            ))
            task_idx += 1

            tasks.append(AgentTask(
                task_id=f"t{task_idx}",
                role=AgentRole.SQL,
                goal=query,
                priority=2
            ))
            task_idx += 1

        # Every technical execution ends with Critic Agent review!
        tasks.append(AgentTask(
            task_id=f"t{task_idx}",
            role=AgentRole.CRITIC,
            goal="ارزیابی کیفی نهایی، امنیت تراکنش، تطابق معماری و عدم تخریب داده‌ها",
            priority=99
        ))

        return tasks


task_decomposer = TaskDecomposer()
