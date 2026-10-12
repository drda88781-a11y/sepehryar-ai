"""
Pydantic API request and response models.
"""
from typing import Optional, Any
from pydantic import BaseModel, Field


class ChatApiRequest(BaseModel):
    query: str = Field(description="پرسش کاربر به زبان فارسی")
    session_id: Optional[str] = Field(default=None, description="شناسه گفتگو برای حافظه مکالمه")
    database: Optional[str] = Field(default=None, description="نام پایگاه داده هدف")
    thinking_mode: Optional[str] = Field(default="balanced", description="سطح تفکر: fast, balanced, deep")


class ChatApiResponse(BaseModel):
    user_query: str
    persian_answer: str
    intent: str
    duration_ms: float
    thinking_duration_ms: float = 0.0
    thinking_summary: Optional[str] = None
    thinking_mode: str = "balanced"
    success: bool
    sql_plan: Optional[dict[str, Any]] = None
    sql_result: Optional[dict[str, Any]] = None
    tools_used: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    reasoning_steps: list[str] = Field(default_factory=list)
    critic_verdict: Optional[str] = None


class SQLQueryApiRequest(BaseModel):
    sql: str = Field(description="دستور SELECT فقط-خواندنی")
    database: Optional[str] = Field(default=None, description="نام دیتابیس")
    max_rows: Optional[int] = Field(default=100, description="حداکثر سقف ردیف‌ها")


class SQLQueryApiResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    duration_ms: float
    is_mock: bool = False


class KnowledgeSearchApiResponse(BaseModel):
    query: str
    total_found: int
    results: list[dict[str, Any]]


class ExportApiRequest(BaseModel):
    format: str = Field(default="csv", description="فرمت خروجی (csv یا json)")
    filename: str = Field(default="export_data.csv", description="نام فایل")
    rows: list[dict[str, Any]] = Field(description="لیست داده‌های ردیفی")


class ExportApiResponse(BaseModel):
    success: bool
    filepath: str
    total_rows: int
    format: str


class HealthStatusApiResponse(BaseModel):
    status: str
    version: str
    environment: str
    offline_strict: bool
    sql_server: str
    database: str
    db_connected: bool = False


class JoinPathApiRequest(BaseModel):
    source_table: str = Field(description="جدول مبدأ")
    target_table: str = Field(description="جدول مقصد")


class JoinedQueryApiRequest(BaseModel):
    tables: list[str] = Field(description="فهرست جداول مورد نیاز برای گزارش")
    select_fields: list[str] = Field(default_factory=list, description="فیلدهای انتخابی")
    where_clauses: list[str] = Field(default_factory=list, description="شروط فیلتر")
    order_by: Optional[str] = Field(default=None, description="مرتب‌سازی")
    top_limit: int = Field(default=50, description="سقف تعداد رکورد")


class MigrationValidationApiRequest(BaseModel):
    records: list[dict[str, Any]] = Field(description="رکوردهای سند افتتاحیه جهت اعتبارسنجی تراز")


class CleanPersonApiRequest(BaseModel):
    name: str = Field(description="نام خام همراه با احتمالی شماره تلفن")
    mobile: Optional[str] = Field(default=None, description="شماره موبایل خام")
    tell: Optional[str] = Field(default=None, description="شماره تلفن ثابت خام")
    is_bank: bool = Field(default=False, description="آیا حساب بانکی است؟")


class CopilotAskApiRequest(BaseModel):
    query: str = Field(description="پرسش فنی، مهندسی یا برنامه‌نویسی درباره سپهریار")


class CopilotScriptApiRequest(BaseModel):
    scenario: str = Field(description="نام سناریو (create_person, create_invoice, disable_triggers)")
    params: dict[str, Any] = Field(default_factory=dict, description="پارامترهای متغیر کد")
    language: str = Field(default="sql", description="زبان اسکریپت (sql یا python)")


class CopilotLintApiRequest(BaseModel):
    scenario: str = Field(default="general", description="نوع عملیات")
    dataset: list[dict[str, Any]] = Field(description="مجموعه داده‌های پیشنهادی جهت بازرسی")


class BrainSolveApiRequest(BaseModel):
    query: str = Field(description="پرسش، تسک مهندسی یا چالش نرم‌افزاری سپهریار")
    session_id: Optional[str] = Field(default="default", description="شناسه نشست")
    database: Optional[str] = Field(default=None, description="نام پایگاه داده هدف")


class BrainSolveApiResponse(BaseModel):
    query: str
    solution_markdown: str
    critic_verdict: Optional[str] = None
    confidence_score: Optional[float] = None
    safety_checks: list[str] = Field(default_factory=list)
    reasoning_steps: list[dict[str, Any]] = Field(default_factory=list)
    generated_sql: Optional[str] = None
    generated_sp: Optional[str] = None
    generated_code: Optional[str] = None
    sub_agents_used: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    success: bool = True


class AgentDirectTaskRequest(BaseModel):
    goal: str = Field(description="هدف یا دستور برای ایجنت تخصصی")
    context: dict[str, Any] = Field(default_factory=dict, description="کانتکست تکمیلی")


class AgentDirectTaskResponse(BaseModel):
    role: str
    summary: str
    findings: list[str] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    success: bool = True


