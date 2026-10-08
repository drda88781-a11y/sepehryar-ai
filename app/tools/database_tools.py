"""
Database tools with strict Pydantic contracts for inspection, relationships, row counts, and safe queries.
"""
from typing import Optional, Any
from pydantic import BaseModel, Field
from app.config.settings import settings
from app.core.exceptions import DatabaseConnectionError
from app.database.connection import db_connection_manager
from app.database.mock_provider import get_mock_sample_rows
from app.database.safe_sql import SafeSQLValidator, safe_sql_executor
from app.database.scanner import database_scanner
from app.storage.repository import storage_repo
from app.tools.registry import register_tool


# --- Pydantic Schemas for Tools ---

class InspectDatabaseInput(BaseModel):
    database_name: Optional[str] = Field(default=None, description="نام دیتابیس (در صورت خالی بودن، دیتابیس پیش‌فرض بررسی می‌شود)")

class InspectDatabaseOutput(BaseModel):
    database_name: str
    server_name: str
    total_tables: int
    tables_summary: list[dict[str, Any]]
    total_views: int
    total_procs: int
    total_triggers: int


class InspectTableInput(BaseModel):
    table_name: str = Field(description="نام جدول مورد نظر (مثلاً TblKala یا TblPerson)")
    database_name: Optional[str] = Field(default=None, description="نام دیتابیس")

class InspectTableOutput(BaseModel):
    table_name: str
    row_count: int
    description: Optional[str] = None
    primary_keys: list[str]
    columns_count: int
    columns: list[dict[str, Any]]
    constraints_count: int
    indexes_count: int
    triggers_count: int


class InspectColumnInput(BaseModel):
    table_name: str = Field(description="نام جدول")
    column_name: str = Field(description="نام ستون")
    database_name: Optional[str] = Field(default=None, description="نام دیتابیس")

class InspectColumnOutput(BaseModel):
    table_name: str
    column_name: str
    data_type: str
    max_length: Optional[int]
    is_nullable: bool
    is_identity: bool
    default_value: Optional[str]
    description: Optional[str]


class FindRelationshipsInput(BaseModel):
    table_name: str = Field(description="نام جدول برای یافتن روابط ورودی و خروجی")
    database_name: Optional[str] = Field(default=None, description="نام دیتابیس")

class FindRelationshipsOutput(BaseModel):
    table_name: str
    outgoing_relationships: list[dict[str, Any]]  # Foreign keys pointing out
    incoming_relationships: list[dict[str, Any]]  # Foreign keys pointing in


class GetTableRowCountInput(BaseModel):
    table_name: str = Field(description="نام جدول")
    database_name: Optional[str] = Field(default=None, description="نام دیتابیس")

class GetTableRowCountOutput(BaseModel):
    table_name: str
    row_count: int


class GetSampleRowsInput(BaseModel):
    table_name: str = Field(description="نام جدول")
    limit: int = Field(default=20, le=100, description="تعداد رکوردهای نمونه (حداکثر ۱۰۰)")
    database_name: Optional[str] = Field(default=None, description="نام دیتابیس")

class GetSampleRowsOutput(BaseModel):
    table_name: str
    columns: list[str]
    rows: list[dict[str, Any]]
    total_returned: int


class ValidateSqlInput(BaseModel):
    sql: str = Field(description="دستور SQL برای اعتبارسنجی امنیتی")

class ValidateSqlOutput(BaseModel):
    is_valid: bool
    error_message: Optional[str] = None


class RunSafeSelectInput(BaseModel):
    sql: str = Field(description="دستور SQL فقط-خواندنی SELECT برای اجرا")
    database_name: Optional[str] = Field(default=None, description="نام دیتابیس")
    limit: int = Field(default=100, le=500, description="حداکثر تعداد ردیف‌ها")

class RunSafeSelectOutput(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    duration_ms: float
    is_mock: bool


# --- Helper to obtain schema ---
def _get_active_schema(database_name: Optional[str]) -> Any:
    db = database_name or settings.sql_database
    # Try retrieving from SQLite cache first
    cached = storage_repo.get_database_metadata(db)
    if cached:
        from app.database.metadata import DatabaseSchema
        return DatabaseSchema(**cached)
    # If not cached, trigger scan
    return database_scanner.scan_database(database=db)


# --- Registered Tools ---

@register_tool(
    name="inspect_database",
    description="بررسی ساختار کلی پایگاه داده، تعداد جداول، ویوها، پروسیجرها و تریگرها",
    category="database",
    input_model=InspectDatabaseInput,
    output_model=InspectDatabaseOutput
)
def inspect_database(database_name: Optional[str] = None) -> InspectDatabaseOutput:
    db = database_name or settings.sql_database
    schema = _get_active_schema(db)

    summary_list = []
    for tbl_name, tbl_meta in schema.tables.items():
        summary_list.append({
            "name": tbl_name,
            "row_count": tbl_meta.row_count,
            "description": tbl_meta.description
        })

    return InspectDatabaseOutput(
        database_name=schema.database_name,
        server_name=schema.server_name,
        total_tables=schema.total_tables,
        tables_summary=summary_list,
        total_views=schema.total_views,
        total_procs=schema.total_procs,
        total_triggers=schema.total_triggers
    )


@register_tool(
    name="inspect_table",
    description="استخراج ساختار تفصیلی یک جدول شامل ستون‌ها، کلیدهای اصلی، ایندکس‌ها و تریگرها",
    category="database",
    input_model=InspectTableInput,
    output_model=InspectTableOutput
)
def inspect_table(table_name: str, database_name: Optional[str] = None) -> InspectTableOutput:
    db = database_name or settings.sql_database
    schema = _get_active_schema(db)

    tbl_meta = schema.tables.get(table_name)
    if not tbl_meta:
        # Case-insensitive search
        for name, meta in schema.tables.items():
            if name.lower() == table_name.lower():
                tbl_meta = meta
                break

    if not tbl_meta:
        raise ValueError(f"جدول '{table_name}' در دیتابیس '{db}' یافت نشد.")

    cols_list = []
    for col_name, col in tbl_meta.columns.items():
        cols_list.append({
            "name": col_name,
            "data_type": col.data_type,
            "max_length": col.max_length,
            "is_nullable": col.is_nullable,
            "is_identity": col.is_identity,
            "description": col.description
        })

    return InspectTableOutput(
        table_name=tbl_meta.name,
        row_count=tbl_meta.row_count,
        description=tbl_meta.description,
        primary_keys=tbl_meta.primary_keys,
        columns_count=len(tbl_meta.columns),
        columns=cols_list,
        constraints_count=len(tbl_meta.constraints),
        indexes_count=len(tbl_meta.indexes),
        triggers_count=len(tbl_meta.triggers)
    )


@register_tool(
    name="inspect_column",
    description="بررسی جزئیات فنی و معنایی یک ستون خاص در جدول",
    category="database",
    input_model=InspectColumnInput,
    output_model=InspectColumnOutput
)
def inspect_column(table_name: str, column_name: str, database_name: Optional[str] = None) -> InspectColumnOutput:
    tbl_out = inspect_table(table_name=table_name, database_name=database_name)
    target_col = None
    for c in tbl_out.columns:
        if c["name"].lower() == column_name.lower():
            target_col = c
            break

    if not target_col:
        raise ValueError(f"ستون '{column_name}' در جدول '{table_name}' وجود ندارد.")

    return InspectColumnOutput(
        table_name=tbl_out.table_name,
        column_name=target_col["name"],
        data_type=target_col["data_type"],
        max_length=target_col.get("max_length"),
        is_nullable=target_col["is_nullable"],
        is_identity=target_col["is_identity"],
        default_value=target_col.get("default_value"),
        description=target_col.get("description")
    )


@register_tool(
    name="find_relationships",
    description="یافتن روابط کلید خارجی رسمی و تخمینی مرتبط با یک جدول",
    category="database",
    input_model=FindRelationshipsInput,
    output_model=FindRelationshipsOutput
)
def find_relationships(table_name: str, database_name: Optional[str] = None) -> FindRelationshipsOutput:
    db = database_name or settings.sql_database
    schema = _get_active_schema(db)

    outgoing = []
    incoming = []
    t_lower = table_name.lower()

    for rel in schema.relationships:
        if rel.source_table.lower() == t_lower:
            outgoing.append({
                "fk_name": rel.fk_name,
                "source_columns": rel.source_columns,
                "target_table": rel.target_table,
                "target_columns": rel.target_columns,
                "is_inferred": rel.is_inferred,
                "description": rel.description
            })
        if rel.target_table.lower() == t_lower:
            incoming.append({
                "fk_name": rel.fk_name,
                "source_table": rel.source_table,
                "source_columns": rel.source_columns,
                "target_columns": rel.target_columns,
                "is_inferred": rel.is_inferred,
                "description": rel.description
            })

    return FindRelationshipsOutput(
        table_name=table_name,
        outgoing_relationships=outgoing,
        incoming_relationships=incoming
    )


@register_tool(
    name="get_table_row_count",
    description="استخراج سریع تعداد کل ردیف‌های یک جدول بدون قفل کردن پایگاه داده",
    category="database",
    input_model=GetTableRowCountInput,
    output_model=GetTableRowCountOutput
)
def get_table_row_count(table_name: str, database_name: Optional[str] = None) -> GetTableRowCountOutput:
    tbl_out = inspect_table(table_name=table_name, database_name=database_name)
    return GetTableRowCountOutput(
        table_name=tbl_out.table_name,
        row_count=tbl_out.row_count
    )


@register_tool(
    name="get_sample_rows",
    description="استخراج چند ردیف نمونه کنترل‌شده و ماسک‌شده از جدول برای تحلیل داده",
    category="database",
    input_model=GetSampleRowsInput,
    output_model=GetSampleRowsOutput
)
def get_sample_rows(table_name: str, limit: int = 20, database_name: Optional[str] = None) -> GetSampleRowsOutput:
    db = database_name or settings.sql_database
    query = f"SELECT TOP ({limit}) * FROM {table_name}"
    res = safe_sql_executor.execute_readonly_query(
        sql=query,
        database=db,
        max_rows=limit,
        mask_sensitive=True
    )
    return GetSampleRowsOutput(
        table_name=table_name,
        columns=res["columns"],
        rows=res["rows"],
        total_returned=res["total_rows"]
    )


@register_tool(
    name="validate_sql",
    description="بررسی امنیتی دستور SQL برای اطمینان از مجاز بودن و فقط-خواندنی بودن آن",
    category="sql",
    input_model=ValidateSqlInput,
    output_model=ValidateSqlOutput
)
def validate_sql(sql: str) -> ValidateSqlOutput:
    is_valid, reason = SafeSQLValidator.validate_query(sql)
    return ValidateSqlOutput(is_valid=is_valid, error_message=reason)


@register_tool(
    name="run_safe_select",
    description="اجرای ایمن و فقط-خواندنی کوئری SELECT با محدودیت زمانی و سقف رکورد",
    category="sql",
    input_model=RunSafeSelectInput,
    output_model=RunSafeSelectOutput
)
def run_safe_select(sql: str, database_name: Optional[str] = None, limit: int = 100) -> RunSafeSelectOutput:
    db = database_name or settings.sql_database
    res = safe_sql_executor.execute_readonly_query(
        sql=sql,
        database=db,
        max_rows=limit,
        mask_sensitive=True
    )
    return RunSafeSelectOutput(
        columns=res["columns"],
        rows=res["rows"],
        total_rows=res["total_rows"],
        duration_ms=res["duration_ms"],
        is_mock=res.get("is_mock", False)
    )
