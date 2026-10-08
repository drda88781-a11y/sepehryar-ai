"""
Audit logging manager ensuring compliance and activity tracking.
Records actions, duration, database targets, and SQL hashes without exposing passwords.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field
from app.core.logger import audit_logger, scrub_credentials, get_logger

logger = get_logger("audit")


class AuditRecord(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user: str = "local_user"
    action: str
    tool: Optional[str] = None
    target_database: Optional[str] = None
    sql_query_hash: Optional[str] = None
    sql_query_preview: Optional[str] = None
    success: bool = True
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def compute_sql_hash(sql: Optional[str]) -> Optional[str]:
    """Compute SHA-256 fingerprint of SQL statement."""
    if not sql:
        return None
    normalized = " ".join(sql.strip().lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def record_audit(
    action: str,
    tool: Optional[str] = None,
    target_database: Optional[str] = None,
    sql_query: Optional[str] = None,
    success: bool = True,
    duration_ms: float = 0.0,
    user: str = "local_user",
    error_message: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> AuditRecord:
    """Create and persist an audit record in logs and database."""
    sql_hash = compute_sql_hash(sql_query)
    preview = scrub_credentials(sql_query[:120] + "...") if sql_query and len(sql_query) > 120 else (scrub_credentials(sql_query) if sql_query else None)

    record = AuditRecord(
        user=user,
        action=action,
        tool=tool,
        target_database=target_database,
        sql_query_hash=sql_hash,
        sql_query_preview=preview,
        success=success,
        duration_ms=round(duration_ms, 2),
        error_message=scrub_credentials(error_message) if error_message else None,
        metadata=metadata or {}
    )

    # 1. Output to audit log file (JSONL format)
    log_line = record.model_dump_json()
    audit_logger.info(log_line)

    # 2. Persist to SQLite if repository is available
    try:
        from app.storage.repository import storage_repo
        storage_repo.save_audit_record(record)
    except Exception as e:
        # Never break main execution if audit DB write fails
        logger.debug(f"Could not persist audit record to SQLite: {e}")

    return record


class AuditTimer:
    """Context manager to measure and record an audited block."""
    def __init__(
        self,
        action: str,
        tool: Optional[str] = None,
        target_database: Optional[str] = None,
        sql_query: Optional[str] = None,
        user: str = "local_user",
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        self.action = action
        self.tool = tool
        self.target_database = target_database
        self.sql_query = sql_query
        self.user = user
        self.metadata = metadata or {}
        self.start_time = 0.0

    def __enter__(self) -> "AuditTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        success = exc_type is None
        err_msg = str(exc_val) if exc_val else None
        record_audit(
            action=self.action,
            tool=self.tool,
            target_database=self.target_database,
            sql_query=self.sql_query,
            success=success,
            duration_ms=duration_ms,
            user=self.user,
            error_message=err_msg,
            metadata=self.metadata
        )
