"""
Pydantic API request and response models.
"""
from typing import Optional, Any
from pydantic import BaseModel, Field


class ChatApiRequest(BaseModel):
    query: str = Field(description="پرسش کاربر به زبان فارسی")
    session_id: Optional[str] = Field(default=None, description="شناسه گفتگو برای حافظه مکالمه")
    database: Optional[str] = Field(default=None, description="نام پایگاه داده هدف")


class ChatApiResponse(BaseModel):
    user_query: str
    persian_answer: str
    intent: str
    duration_ms: float
    success: bool
    sql_plan: Optional[dict[str, Any]] = None
    sql_result: Optional[dict[str, Any]] = None
    tools_used: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


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
