"""
Database Agent: Specialist in Sepehryar database structures, schema graph,
tables, columns, primary/foreign keys, views, functions, triggers, and dependencies.
"""
import time
from typing import Optional, Any
from app.agent.specialized.base import BaseSpecializedAgent, AgentRole, AgentTask, AgentResult, Blackboard
from app.database.schema_graph import schema_graph, SEPEHRYAR_TABLE_CARDS, TableIdentityCard
from app.database.metadata import SEPEHRYAR_TABLE_DICTIONARY, SEPEHRYAR_COLUMN_DICTIONARY
from app.storage.repository import storage_repo
from app.core.logger import get_logger

logger = get_logger("agent.database_agent")


class DatabaseAgent(BaseSpecializedAgent):
    """
    Expert on Sepehryar SQL Server Database:
    - Tables & Columns inspection
    - Primary Keys & Foreign Keys (physical and logical ERP conventions)
    - Relationships mapping & Join paths
    - Views, Triggers, and Stored Procedures analysis
    - Dependencies extraction
    - Discovering similar structures
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.DATABASE,
            persian_title="متخصص دیتابیس سپهریار",
            description="تحلیل عمیق جداول، فیلدها، کلیدها، تریگرها، ایندکس‌ها، ویوها و گراف وابستگی‌های دیتابیس سپهریار."
        )

    def execute(self, task: AgentTask, blackboard: Blackboard) -> AgentResult:
        start_time = time.perf_counter()
        blackboard.add_step(
            self.role,
            "کشف و تحلیل ساختار دیتابیس",
            f"بررسی اسکیما، جداول مرتبط، کلیدها و تریگرها برای هدف: '{task.goal}'"
        )

        query = task.goal.lower()
        findings: list[str] = []
        artifacts: dict[str, Any] = {}
        warnings: list[str] = []

        # 1. Identify relevant tables from query & blackboard
        identified_tables: list[str] = list(blackboard.target_entities)
        for tbl_name, card in SEPEHRYAR_TABLE_CARDS.items():
            if (
                tbl_name.lower() in query
                or card.persian_title.lower() in query
                or any(w in query for w in card.persian_title.lower().split() if len(w) > 3)
            ):
                if tbl_name not in identified_tables:
                    identified_tables.append(tbl_name)

        # Domain keyword enricher
        if any(w in query for w in ["اشخاص", "مشتری", "تامین", "طرف", "پرسنل", "بانک", "person", "شخص"]):
            for t in ["TblPerson", "Master"]:
                if t not in identified_tables:
                    identified_tables.append(t)
        if any(w in query for w in ["کالا", "انبار", "موجودی", "بارکد", "item", "kala"]):
            for t in ["TblKala", "TblAnbar"]:
                if t not in identified_tables:
                    identified_tables.append(t)
        if any(w in query for w in ["سند", "آرتیکل", "بدهکار", "بستانکار", "تراز", "sanad"]):
            for t in ["TblSanad", "TR"]:
                if t not in identified_tables:
                    identified_tables.append(t)
        if any(w in query for w in ["فاکتور", "فروش", "خرید", "تراکنش", "factor"]):
            for t in ["TR", "TblTypeTR"]:
                if t not in identified_tables:
                    identified_tables.append(t)
        if any(w in query for w in ["چک", "صیاد", "دریافتنی", "پرداختنی", "check"]):
            for t in ["Check", "CheckPardakht"]:
                if t not in identified_tables:
                    identified_tables.append(t)

        if not identified_tables:
            identified_tables.extend(["Master", "TR", "TblPerson"])

        artifacts["target_tables"] = identified_tables
        blackboard.target_entities = list(set(blackboard.target_entities + identified_tables))

        # 2. Extract detailed table cards, columns, keys and triggers
        table_details = []
        for tbl in identified_tables:
            card = SEPEHRYAR_TABLE_CARDS.get(tbl)
            if card:
                pks = ", ".join(card.primary_keys) or "نامشخص"
                vitals = ", ".join(card.vital_columns[:6])
                indexes = ", ".join(card.indexed_columns)
                desc = (
                    f"جدول **{card.table_name}** ({card.persian_title}) | "
                    f"دسته‌بندی: `{card.category}` | کلید اصلی: `{pks}` | ستون‌های کلیدی: `{vitals}` | ایندکس‌ها: `{indexes}`"
                )
                findings.append(desc)
                table_details.append({
                    "table_name": card.table_name,
                    "title": card.persian_title,
                    "category": card.category,
                    "primary_keys": card.primary_keys,
                    "vital_columns": card.vital_columns,
                    "business_notes": card.business_notes
                })
            else:
                findings.append(f"جدول پویا کشف‌شده: **{tbl}**")

        artifacts["table_details"] = table_details

        # 3. Analyze relationships and join paths between identified tables
        join_paths = []
        if len(identified_tables) >= 2:
            root = identified_tables[0]
            for target in identified_tables[1:]:
                path = schema_graph.find_join_path(root, target)
                if path:
                    for edge in path:
                        join_stmt = f"{edge.join_type} {edge.target_table} ON {edge.join_condition} ({edge.description})"
                        if join_stmt not in join_paths:
                            join_paths.append(join_stmt)
                            findings.append(f"مسیر ارتباطی دیتابیس: `{join_stmt}`")

        artifacts["join_paths"] = join_paths

        # 4. Check critical triggers and database gotchas
        for tbl in identified_tables:
            if tbl.upper() == "TR":
                warnings.append("تریگر هماهنگ‌سازی و لاگ روی جدول TR فعال است؛ هرگونه تغییر دسته‌ای باید با آگاهی از فیلدهای سند SanadM و اقلام کالا باشد.")
            if tbl.upper() in ["TBLSANAD", "TR", "MASTER"]:
                warnings.append("تراز بودن مجموع ستون‌های Bed و Bes در اسناد حسابداری و دفتر روزنامه الزامی است (Bed == Bes).")
            if tbl.upper() == "TBLPERSON":
                warnings.append("فیلد Type در TblPerson تفکیک‌کننده ماهیت است: ۱=مشتری، ۲=تامین‌کننده، ۴=بانک/صندوق. فیلد Sh_ozviat باید یونیک بماند.")

        duration = (time.perf_counter() - start_time) * 1000
        summary = f"تحلیل دیتابیس برای {len(identified_tables)} جدول کلیدی ({', '.join(identified_tables)}) با موفقیت انجام شد."

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
