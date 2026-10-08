"""
REST API route definitions for Sepehryar AI Engine.
"""
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.agent.orchestrator import agent_orchestrator
from app.api.models import (
    ChatApiRequest,
    ChatApiResponse,
    SQLQueryApiRequest,
    SQLQueryApiResponse,
    KnowledgeSearchApiResponse,
    ExportApiRequest,
    ExportApiResponse,
    HealthStatusApiResponse,
)
from app.api.security import verify_api_token
from app.config.settings import settings
from app.database.safe_sql import safe_sql_executor
from app.diagnostics.checks import run_full_system_diagnosis
from app.knowledge.search import knowledge_search_engine
from app.storage.repository import storage_repo
from app.tools.export import data_exporter

router = APIRouter()


@router.get("/health", response_model=HealthStatusApiResponse, tags=["System"])
def get_health() -> HealthStatusApiResponse:
    """Liveness probe - public local endpoint without authentication."""
    return HealthStatusApiResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.app_env,
        offline_strict=settings.offline_strict,
        sql_server=settings.sql_server,
        database=settings.sql_database
    )


@router.get("/api/system/health", tags=["System"], dependencies=[Depends(verify_api_token)])
def get_system_diagnostics():
    """Detailed hardware and database health diagnostics report."""
    report = run_full_system_diagnosis()
    return report.model_dump()


@router.post("/api/chat", response_model=ChatApiResponse, tags=["AI Agent"], dependencies=[Depends(verify_api_token)])
def chat_with_agent(req: ChatApiRequest) -> ChatApiResponse:
    """Send natural language query to the Sepehryar AI Agent."""
    if not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="متن پرسش نمی‌تواند خالی باشد."
        )

    res = agent_orchestrator.process_query(
        query=req.query,
        session_id=req.session_id,
        database_name=req.database
    )

    sql_plan_dict = res.sql_plan.model_dump() if res.sql_plan else None
    tools_list = [t.model_dump() for t in res.tools_used]

    return ChatApiResponse(
        user_query=res.user_query,
        persian_answer=res.persian_answer,
        intent=res.intent.value,
        duration_ms=res.duration_ms,
        success=res.success,
        sql_plan=sql_plan_dict,
        sql_result=res.sql_result,
        tools_used=tools_list,
        sources=res.sources
    )


@router.post("/api/sql/execute-readonly", response_model=SQLQueryApiResponse, tags=["Database"], dependencies=[Depends(verify_api_token)])
def execute_readonly_sql(req: SQLQueryApiRequest) -> SQLQueryApiResponse:
    """Execute a safe, validated read-only SQL query."""
    target_db = req.database or settings.sql_database
    max_rows = req.max_rows or settings.sql_max_rows

    try:
        res = safe_sql_executor.execute_readonly_query(
            sql=req.sql,
            database=target_db,
            max_rows=max_rows,
            mask_sensitive=True
        )
        return SQLQueryApiResponse(
            columns=res["columns"],
            rows=res["rows"],
            total_rows=res["total_rows"],
            duration_ms=res["duration_ms"],
            is_mock=res.get("is_mock", False)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"خطا در اجرای کوئری فقط-خواندنی: {str(e)}"
        )


@router.get("/api/database/schema", tags=["Database"], dependencies=[Depends(verify_api_token)])
def get_database_schema(database: Optional[str] = Query(default=None)):
    """Retrieve scanned database metadata and tables summary."""
    target_db = database or settings.sql_database
    meta = storage_repo.get_database_metadata(target_db)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"متادیتای پایگاه داده '{target_db}' در حافظه محلی یافت نشد. لطفاً ابتدا اسکن دیتابیس را اجرا کنید."
        )

    # Return summary
    tables_summary = [
        {
            "name": name,
            "row_count": info.get("row_count", 0),
            "columns_count": len(info.get("columns", {})),
            "description": info.get("description")
        }
        for name, info in meta.get("tables", {}).items()
    ]
    return {
        "database_name": meta.get("database_name", target_db),
        "total_tables": len(tables_summary),
        "tables": tables_summary,
        "views_count": len(meta.get("views", [])),
        "procedures_count": len(meta.get("stored_procedures", []))
    }


@router.get("/api/knowledge/search", response_model=KnowledgeSearchApiResponse, tags=["Knowledge Base"], dependencies=[Depends(verify_api_token)])
def search_knowledge(
    q: str = Query(description="عبارت جستجو"),
    category: Optional[str] = Query(default=None, description="دسته‌بندی"),
    limit: int = Query(default=5, ge=1, le=20)
) -> KnowledgeSearchApiResponse:
    cat_str = category if isinstance(category, str) else None
    limit_val = limit if isinstance(limit, int) else 5
    results = knowledge_search_engine.search(query=q, category=cat_str, limit=limit_val)
    formatted = [
        {
            "doc_title": r.doc_title,
            "heading": r.heading,
            "category": r.category,
            "snippet": r.snippet,
            "score": r.score,
            "filepath": r.filepath
        }
        for r in results
    ]
    return KnowledgeSearchApiResponse(
        query=q,
        total_found=len(results),
        results=formatted
    )


@router.post("/api/export", response_model=ExportApiResponse, tags=["Export"], dependencies=[Depends(verify_api_token)])
def export_data_endpoint(req: ExportApiRequest) -> ExportApiResponse:
    """Export tabular rows to CSV (with UTF-8 BOM) or JSON on the local system."""
    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    target_path = export_dir / req.filename

    fmt = req.format.lower().strip()
    if fmt == "json":
        saved = data_exporter.export_to_json(req.rows, target_path)
    else:
        saved = data_exporter.export_to_csv(req.rows, target_path)

    return ExportApiResponse(
        success=True,
        filepath=saved,
        total_rows=len(req.rows),
        format=fmt
    )
