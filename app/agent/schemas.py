"""
Pydantic schemas for Agent intent detection, SQL planning, and structured execution outputs.
"""
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class UserIntent(str, Enum):
    DATABASE_QUERY = "database_query"       # Questions asking about data, tables, counts, balances
    SCHEMA_INSPECTION = "schema_inspection" # Questions asking about table structures, relationships, columns
    TROUBLESHOOTING = "troubleshooting"     # Error diagnosis, SQL Server connection failures
    SYSTEM_HEALTH = "system_health"         # CPU, RAM, Disk, Services status
    GENERAL_ACCOUNTING = "general_accounting" # Accounting concepts, Sepehryar workflows
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IntentDetectionResult(BaseModel):
    intent: UserIntent = UserIntent.DATABASE_QUERY
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    requires_database: bool = True
    requires_knowledge: bool = False
    requires_tools: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    extracted_entities: list[str] = Field(default_factory=list)  # e.g. ["TblKala", "TblPerson"]
    summary_reasoning: Optional[str] = None


class SQLPlan(BaseModel):
    goal: str = Field(description="هدف استخراج داده به زبان فارسی")
    target_tables: list[str] = Field(default_factory=list, description="جداول هدف")
    target_columns: list[str] = Field(default_factory=list, description="ستون‌های مورد نیاز")
    where_filters: list[str] = Field(default_factory=list, description="شروط فیلتر")
    joins: list[str] = Field(default_factory=list, description="روابط اتصال جداول")
    order_by: Optional[str] = None
    row_limit: int = 100
    generated_sql: str = Field(description="دستور SQL نهایی تولید شده")
    is_readonly: bool = True
    risk_level: RiskLevel = RiskLevel.LOW
    validation_status: bool = False
    validation_message: Optional[str] = None


class ToolCallLog(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    success: bool = True
    output_summary: Optional[str] = None


class AgentResponse(BaseModel):
    user_query: str
    persian_answer: str
    intent: UserIntent
    sql_plan: Optional[SQLPlan] = None
    sql_result: Optional[dict[str, Any]] = None
    tools_used: list[ToolCallLog] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    thinking_duration_ms: float = 0.0
    thinking_summary: Optional[str] = None
    thinking_mode: str = "balanced"
    success: bool = True
    error_details: Optional[str] = None
    master_solution: Optional[str] = None
    critic_verdict: Optional[str] = None
    reasoning_steps: list[str] = Field(default_factory=list)
