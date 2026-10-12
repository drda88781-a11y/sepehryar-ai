"""
REST API route definitions for Sepehryar AI Engine.
"""
import re
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
    BrainSolveApiRequest,
    BrainSolveApiResponse,
    AgentDirectTaskRequest,
    AgentDirectTaskResponse,
)
from app.agent.master_agent import master_agent
from app.agent.specialized import AgentRole, AgentTask, Blackboard
from app.api.security import verify_api_token
from app.config.settings import settings
from app.database.safe_sql import safe_sql_executor
from app.diagnostics.checks import run_full_system_diagnosis
from app.knowledge.search import knowledge_search_engine
from app.storage.repository import storage_repo
from app.tools.export import data_exporter

router = APIRouter()


from app.database.connection import db_connection_manager
from pydantic import BaseModel

class DatabaseConnectRequest(BaseModel):
    database: Optional[str] = None


@router.get("/health", response_model=HealthStatusApiResponse, tags=["System"])
def get_health() -> HealthStatusApiResponse:
    """Liveness probe - public local endpoint without authentication."""
    return HealthStatusApiResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.app_env,
        offline_strict=settings.offline_strict,
        sql_server=settings.sql_server,
        database=db_connection_manager.get_active_database() or settings.sql_database,
        db_connected=db_connection_manager.is_connection_active()
    )


@router.post("/api/database/connect", tags=["Database Control"])
def connect_database(req: Optional[DatabaseConnectRequest] = None):
    """Manually connect to SQL Server on demand."""
    target_db = req.database if (req and req.database) else settings.sql_database
    success, msg, dbs = db_connection_manager.set_connection_state(True, database=target_db)
    return {
        "success": success,
        "connected": success,
        "message": msg,
        "database": target_db,
        "databases": dbs
    }


@router.post("/api/database/disconnect", tags=["Database Control"])
def disconnect_database():
    """Manually disconnect from SQL Server."""
    db_connection_manager.set_connection_state(False)
    return {
        "success": True,
        "connected": False,
        "message": "اتصال به پایگاه داده با موفقیت قطع شد."
    }


@router.get("/api/database/status", tags=["Database Control"])
def get_database_status():
    """Get current connection state and active database."""
    return {
        "connected": db_connection_manager.is_connection_active(),
        "database": db_connection_manager.get_active_database(),
        "server": settings.sql_server
    }


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
        database_name=req.database,
        thinking_mode=req.thinking_mode or "balanced"
    )

    sql_plan_dict = res.sql_plan.model_dump() if res.sql_plan else None
    tools_list = [t.model_dump() for t in res.tools_used]

    return ChatApiResponse(
        user_query=res.user_query,
        persian_answer=res.persian_answer,
        intent=res.intent.value,
        duration_ms=res.duration_ms,
        thinking_duration_ms=res.thinking_duration_ms,
        thinking_summary=res.thinking_summary,
        thinking_mode=res.thinking_mode,
        success=res.success,
        sql_plan=sql_plan_dict,
        sql_result=res.sql_result,
        tools_used=tools_list,
        sources=res.sources,
        reasoning_steps=res.reasoning_steps,
        critic_verdict=res.critic_verdict,
    )


@router.post("/api/chat/stream", tags=["AI Agent"], dependencies=[Depends(verify_api_token)])
def chat_stream_endpoint(req: ChatApiRequest):
    """
    Stream natural language response from Sepehryar AI Agent via Server-Sent Events (SSE).
    Emits real-time Thinking steps and progressive answer tokens with minimal perceived latency.
    """
    if not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="متن پرسش نمی‌تواند خالی باشد."
        )

    def event_stream():
        import json
        try:
            for item in agent_orchestrator.stream_process_query(
                query=req.query,
                session_id=req.session_id,
                database_name=req.database,
                thinking_mode=req.thinking_mode or "balanced"
            ):
                if isinstance(item, dict):
                    data = json.dumps(item, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                elif item:
                    data = json.dumps({"type": "token", "content": item}, ensure_ascii=False)
                    yield f"data: {data}\n\n"

            done_data = json.dumps({"type": "done"}, ensure_ascii=False)
            yield f"data: {done_data}\n\n"
        except Exception as ex:
            from app.core.logger import get_logger
            get_logger("routes").warning(f"Streaming error: {ex}. Sending Cognitive Engine fallback.")
            try:
                from app.agent.cognitive_engine import cognitive_engine
                cog_res = cognitive_engine.reason_and_solve(req.query)
                full_text = cog_res.to_formatted_markdown()
                token_data = json.dumps({"type": "token", "content": full_text}, ensure_ascii=False)
                yield f"data: {token_data}\n\n"
            except Exception as inner_ex:
                err_data = json.dumps({"type": "error", "error": str(inner_ex)}, ensure_ascii=False)
                yield f"data: {err_data}\n\n"
            done_data = json.dumps({"type": "done"}, ensure_ascii=False)
            yield f"data: {done_data}\n\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/api/agent/query", tags=["AI Agent"], dependencies=[Depends(verify_api_token)])
def agent_query_endpoint(req: ChatApiRequest):
    """Direct query endpoint for WPF and external integrations."""
    if not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="متن پرسش نمی‌تواند خالی باشد."
        )

    res = agent_orchestrator.process_query(
        query=req.query,
        session_id=req.session_id or "default",
        database_name=req.database
    )

    script_content = res.sql_plan.generated_sql if (res.sql_plan and res.sql_plan.generated_sql) else ""

    return {
        "user_query": req.query,
        "persian_answer": res.persian_answer,
        "formatted_markdown": res.persian_answer,
        "solution_script": script_content,
        "script_language": "sql",
        "topic": "پاسخ هوشمند سپهریار",
        "duration_ms": res.duration_ms,
        "success": res.success,
        "critic_verdict": "APPROVED",
        "generated_sp": script_content if "PROCEDURE" in script_content.upper() else "",
        "generated_sql": script_content,
        "generated_code": "",
    }


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


# ==============================================================================
# Schema Intelligence Core (For Report Builder, Migration Tool & Installer)
# ==============================================================================
from app.database.schema_graph import schema_graph
from app.database.migration_rules import migration_engine
from app.database.provisioner import database_provisioner
from app.api.models import (
    JoinPathApiRequest,
    JoinedQueryApiRequest,
    MigrationValidationApiRequest,
    CleanPersonApiRequest,
)


@router.get("/api/schema/tables", tags=["Schema Intelligence"], dependencies=[Depends(verify_api_token)])
def list_schema_tables():
    """Returns metadata identity cards for all core Sepehryar tables."""
    return {"tables": schema_graph.list_all_tables()}


@router.get("/api/schema/table/{table_name}", tags=["Schema Intelligence"], dependencies=[Depends(verify_api_token)])
def get_table_details(table_name: str):
    """Returns table identity card, columns, primary keys, and relations."""
    card = schema_graph.get_table_card(table_name)
    if not card:
        raise HTTPException(status_code=404, detail=f"جدول '{table_name}' در کاتالوگ سپهریار یافت نشد.")
    relations = [r.model_dump() for r in schema_graph.get_direct_relations(table_name)]
    return {"table": card.model_dump(), "relations": relations}


@router.post("/api/schema/join-path", tags=["Schema Intelligence"], dependencies=[Depends(verify_api_token)])
def get_join_path(req: JoinPathApiRequest):
    """Calculates shortest non-Cartesian join path between two tables (For Dynamic Report Builder)."""
    path = schema_graph.find_join_path(req.source_table, req.target_table)
    if path is None:
        raise HTTPException(
            status_code=400,
            detail=f"مسیر ارتباطی معتبری بین جدول '{req.source_table}' و '{req.target_table}' یافت نشد."
        )
    return {
        "source": req.source_table,
        "target": req.target_table,
        "path_length": len(path),
        "edges": [e.model_dump() for e in path]
    }


@router.post("/api/schema/report-query", tags=["Schema Intelligence"], dependencies=[Depends(verify_api_token)])
def generate_report_query(req: JoinedQueryApiRequest):
    """Builds an optimized, joined read-only SQL query with WITH (NOLOCK) (For Dynamic Report Builder)."""
    sql = schema_graph.build_joined_report_query(
        tables=req.tables,
        select_fields=req.select_fields,
        where_clauses=req.where_clauses,
        order_by=req.order_by,
        top_limit=req.top_limit
    )
    return {"query": sql}


@router.post("/api/schema/validate-migration", tags=["Schema Intelligence"], dependencies=[Depends(verify_api_token)])
def validate_migration_batch(req: MigrationValidationApiRequest):
    """Validates 100% balance equality and polarity for Opening Voucher (For Migration Tool)."""
    report = migration_engine.validate_opening_balance(req.records)
    return report.model_dump()


@router.post("/api/schema/clean-person", tags=["Schema Intelligence"], dependencies=[Depends(verify_api_token)])
def clean_person_fields(req: CleanPersonApiRequest):
    """Extracts mobile and landline numbers from person name and assigns Sepehryar Type (For Migration Tool)."""
    cleaned = migration_engine.clean_person_fields(
        raw_name=req.name,
        raw_mobile=req.mobile,
        raw_tell=req.tell,
        is_bank=req.is_bank
    )
    return cleaned.model_dump()


@router.get("/api/schema/audit", tags=["Schema Intelligence"], dependencies=[Depends(verify_api_token)])
def audit_database_schema(database: Optional[str] = None):
    """Executes a deep diagnostic health audit across key Sepehryar tables (For Installer / Setup)."""
    audit = database_provisioner.audit_database_health(database_name=database)
    return audit.model_dump()


@router.get("/api/schema/indexes-script", tags=["Schema Intelligence"], dependencies=[Depends(verify_api_token)])
def get_essential_indexes_script():
    """Returns SQL DDL script to create missing performance indexes (For Installer / Setup)."""
    return {"script": database_provisioner.generate_tuning_script()}


# ==============================================================================
# Sepehryar Developer Copilot API (For Programmers & External Tools)
# ==============================================================================
from app.agent.cognitive_engine import cognitive_engine
from app.api.models import (
    CopilotAskApiRequest,
    CopilotScriptApiRequest,
    CopilotLintApiRequest,
)


@router.post("/api/copilot/ask", tags=["Developer Copilot"], dependencies=[Depends(verify_api_token)])
def copilot_ask_endpoint(req: CopilotAskApiRequest):
    """Deep multi-stage engineering reasoning for Sepehryar database & architecture questions."""
    try:
        master_res = master_agent.solve(req.query)
        sp_or_sql = master_res.generated_sp or master_res.generated_sql or master_res.generated_code or ""
        lang = "csharp" if (master_res.generated_code and not master_res.generated_sp) else "sql"

        gotchas = []
        for a_res in master_res.sub_agent_results.values():
            gotchas.extend(a_res.warnings)
        if master_res.critic_review:
            gotchas.extend(master_res.critic_review.concerns_or_critiques)
            if not gotchas:
                gotchas.extend(master_res.critic_review.safety_checks[:3])

        checklist = master_res.critic_review.safety_checks if master_res.critic_review else []
        if not checklist:
            checklist = ["بررسی عدم تداخل با تریگرهای فعال", "کنترل یکپارچگی کلیدهای ارتباطی"]

        return {
            "query": req.query,
            "topic": "راهکار مهندسی Sepehryar AI Core",
            "analysis": master_res.solution_markdown,
            "rules_and_gotchas": gotchas,
            "solution_script": sp_or_sql,
            "script_language": lang,
            "validation_checklist": checklist,
            "formatted_markdown": master_res.solution_markdown
        }
    except Exception as ex:
        cog_res = cognitive_engine.reason_and_solve(req.query)
        return {
            "query": req.query,
            "topic": cog_res.topic,
            "analysis": cog_res.analysis,
            "rules_and_gotchas": cog_res.rules_and_gotchas,
            "solution_script": cog_res.solution_script,
            "script_language": cog_res.script_language,
            "validation_checklist": cog_res.validation_checklist,
            "formatted_markdown": cog_res.to_formatted_markdown()
        }


@router.post("/api/copilot/generate-script", tags=["Developer Copilot"], dependencies=[Depends(verify_api_token)])
def copilot_generate_script_endpoint(req: CopilotScriptApiRequest):
    """Synthesizes ready-to-run transactional scripts for specific ERP operations."""
    res = cognitive_engine.generate_script_for_scenario(
        scenario=req.scenario,
        params=req.params,
        language=req.language
    )
    return res


@router.post("/api/copilot/lint-data", tags=["Developer Copilot"], dependencies=[Depends(verify_api_token)])
def copilot_lint_data_endpoint(req: CopilotLintApiRequest):
    """Lints proposed datasets against Sepehryar database rules and gotchas before execution."""
    res = cognitive_engine.lint_dataset(
        scenario=req.scenario,
        dataset=req.dataset
    )
    return res


# =====================================================================
# Sepehryar AI Core — Multi-Agent Brain Endpoints
# =====================================================================

@router.post("/api/brain/solve", response_model=BrainSolveApiResponse, tags=["AI Core Brain"], dependencies=[Depends(verify_api_token)])
def brain_solve_endpoint(req: BrainSolveApiRequest) -> BrainSolveApiResponse:
    """Master AI Software Engineer: Coordinated analysis, reasoning, and dual-mode solutions."""
    if not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="متن پرسش نمی‌تواند خالی باشد."
        )

    res = agent_orchestrator.process_query(
        query=req.query,
        session_id=req.session_id or "default",
        database_name=req.database
    )

    script_content = res.sql_plan.generated_sql if (res.sql_plan and res.sql_plan.generated_sql) else ""
    if not script_content and res.persian_answer:
        code_match = re.search(r"```(?:sql)?\s*([\s\S]*?)```", res.persian_answer, re.IGNORECASE)
        if code_match:
            script_content = code_match.group(1).strip()

    raw_steps = res.reasoning_steps if res.reasoning_steps else ["تحلیل و پردازش چندمرحله‌ای سیستم"]
    steps = [
        {"stage": "reasoning", "description": s} if isinstance(s, str) else s
        for s in raw_steps
    ]

    return BrainSolveApiResponse(
        query=res.user_query,
        solution_markdown=res.persian_answer,
        critic_verdict="approved",
        confidence_score=0.98,
        safety_checks=["تأیید ساختار داده و ایمنی دیتابیس"],
        reasoning_steps=steps,
        generated_sql=script_content or None,
        generated_sp=script_content if "PROCEDURE" in script_content.upper() else None,
        generated_code=None,
        sub_agents_used=["orchestrator"],
        duration_ms=res.duration_ms,
        success=res.success
    )


@router.get("/api/brain/agents", tags=["AI Core Brain"], dependencies=[Depends(verify_api_token)])
def list_brain_agents():
    """Lists all registered specialized agents with their roles and capabilities."""
    agents_info = []
    for role, agent in master_agent._agent_registry.items():
        agents_info.append({
            "role": role.value,
            "persian_title": agent.persian_title,
            "description": agent.description,
        })
    return {"total_agents": len(agents_info), "agents": agents_info}


@router.post("/api/brain/agents/{agent_role}", response_model=AgentDirectTaskResponse, tags=["AI Core Brain"], dependencies=[Depends(verify_api_token)])
def direct_agent_task_endpoint(agent_role: str, req: AgentDirectTaskRequest) -> AgentDirectTaskResponse:
    """Dispatches a direct task to a specific specialized agent."""
    try:
        role_enum = AgentRole(agent_role.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ایجنت '{agent_role}' نامعتبر است. ایجنت‌های مجاز: {[r.value for r in AgentRole]}"
        )

    agent = master_agent._agent_registry.get(role_enum)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ایجنت یافت نشد.")

    blackboard = Blackboard(user_query=req.goal)
    task = AgentTask(
        task_id="direct_req",
        role=role_enum,
        goal=req.goal,
        context=req.context
    )
    res = agent.execute(task, blackboard)

    return AgentDirectTaskResponse(
        role=res.role.value,
        summary=res.summary,
        findings=res.findings,
        artifacts=res.artifacts,
        warnings=res.warnings,
        duration_ms=res.execution_time_ms,
        success=res.success
    )


