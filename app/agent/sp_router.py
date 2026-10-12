"""
Native Sepehryar Stored Procedures Router:
Discovers, maps, and securely executes pre-compiled reporting stored procedures.
"""
from typing import Optional, Any
from app.agent.schemas import SQLPlan
from app.core.logger import get_logger

logger = get_logger("agent.sp_router")


class StoredProcedureMetadata:
    def __init__(self, name: str, title: str, description: str, keywords: list[str]):
        self.name = name
        self.title = title
        self.description = description
        self.keywords = keywords


# Registry of approved read-only native Sepehryar reporting stored procedures
NATIVE_REPORTING_PROCEDURES = [
    StoredProcedureMetadata(
        name="_ssp_ListManfiKala",
        title="لیست کالاهای با موجودی منفی",
        description="استخراج فهرست اقلامی که موجودی آنها در انبار منفی شده است",
        keywords=["منفی", "موجودی منفی", "کسری انبار", "کالای منفی", "انبار منفی"]
    ),
    StoredProcedureMetadata(
        name="_ssp_GardeshSood",
        title="گردش و گزارش سود",
        description="تحلیل گردش سود و زیان بازرگانی",
        keywords=["گردش سود", "سود و زیان", "سود ناخالص", "سودآوری"]
    ),
    StoredProcedureMetadata(
        name="_ssp_AmalKardForosh",
        title="گزارش عملکرد و فروش",
        description="خلاصه آمار و عملکرد فروش و فاکتورها",
        keywords=["عملکرد فروش", "امار فروش", "آمار فروش", "گزارش فروش"]
    ),
    StoredProcedureMetadata(
        name="_ssp_MoghayeratAnbar",
        title="مغایرت‌های انبار",
        description="بررسی مغایرت‌های تعدادی و ریالی کاردکس و انبار",
        keywords=["مغایرت انبار", "مغایرت کاردکس", "اختلاف انبار"]
    ),
    StoredProcedureMetadata(
        name="_ssp_FactorNoTaraz",
        title="فاکتورهای نامتوازن",
        description="شناسایی فاکتورهایی که تراز بدهکار و بستانکار آنها تراز نیست",
        keywords=["فاکتور نامتوازن", "فاکتور بی تراز", "فاکتور نامتعادل"]
    ),
    StoredProcedureMetadata(
        name="_ssp_FactorTekrari",
        title="فاکتورهای تکراری",
        description="شناسایی فاکتورهای ثبت شده تکراری در سیستم",
        keywords=["فاکتور تکراری", "فاکتورهای تکراری", "شماره فاکتور تکراری"]
    ),
    StoredProcedureMetadata(
        name="_ssp_EkhtelafCheckVam",
        title="مغایرت چک و وام",
        description="بررسی عدم تطابق‌های اسناد دریافتنی و اقساط",
        keywords=["مغایرت چک", "مغایرت وام", "اختلاف چک"]
    ),
]


class SPRouter:
    """Intelligently matches user queries with native ERP stored procedures."""

    @classmethod
    def match_procedure(cls, query: str) -> Optional[StoredProcedureMetadata]:
        """Find matching native stored procedure based on Persian accounting keywords."""
        q_norm = query.replace("ي", "ی").replace("ك", "ک").lower()
        for sp in NATIVE_REPORTING_PROCEDURES:
            for kw in sp.keywords:
                if kw in q_norm:
                    logger.info(f"SPRouter matched query '{query}' to procedure: {sp.name}")
                    return sp
        return None

    @classmethod
    def build_plan(cls, sp: StoredProcedureMetadata) -> SQLPlan:
        """Create a validated execution plan for the matched stored procedure."""
        sql = f"EXEC dbo.{sp.name}"
        return SQLPlan(
            goal=f"اجرای پروسیجر گزارش‌گیری سپهریار: {sp.title}",
            target_tables=[sp.name],
            target_columns=["*"],
            generated_sql=sql,
            validation_status=True,
            row_limit=50
        )


sp_router = SPRouter()
