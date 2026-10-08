"""
Data models and DDL schemas for local SQLite storage.
"""
from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field

# SQLite Table DDL definitions
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS connections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    server TEXT NOT NULL,
    instance TEXT,
    database TEXT NOT NULL,
    auth_type TEXT NOT NULL DEFAULT 'windows',
    username TEXT,
    encrypted_password TEXT,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS database_metadata (
    id TEXT PRIMARY KEY,
    database_name TEXT NOT NULL UNIQUE,
    server_name TEXT NOT NULL,
    scanned_at TEXT NOT NULL,
    tables_count INTEGER NOT NULL DEFAULT 0,
    views_count INTEGER NOT NULL DEFAULT 0,
    procs_count INTEGER NOT NULL DEFAULT 0,
    triggers_count INTEGER NOT NULL DEFAULT 0,
    schema_version TEXT DEFAULT '1.0',
    metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    filepath TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    doc_metadata_json TEXT,
    indexed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    doc_title TEXT NOT NULL,
    category TEXT NOT NULL,
    heading TEXT NOT NULL,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    filepath TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON knowledge_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_category ON knowledge_chunks(category);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    database_context TEXT,
    messages_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user TEXT NOT NULL,
    action TEXT NOT NULL,
    tool TEXT,
    target_database TEXT,
    sql_query_hash TEXT,
    sql_query_preview TEXT,
    success INTEGER NOT NULL,
    duration_ms REAL NOT NULL,
    error_message TEXT,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS diagnostic_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL,
    summary TEXT NOT NULL,
    details_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    input_json TEXT NOT NULL,
    output_json TEXT NOT NULL,
    success INTEGER NOT NULL,
    duration_ms REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_metadata_dbname ON database_metadata(database_name);
CREATE INDEX IF NOT EXISTS idx_connections_name ON connections(name);
"""


class DBConnectionConfig(BaseModel):
    id: Optional[str] = None
    name: str
    server: str
    instance: Optional[str] = None
    database: str
    auth_type: str = "windows"  # 'windows' or 'sql'
    username: Optional[str] = ""
    encrypted_password: Optional[str] = ""
    is_default: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ScannedDatabaseRecord(BaseModel):
    id: Optional[str] = None
    database_name: str
    server_name: str
    scanned_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tables_count: int = 0
    views_count: int = 0
    procs_count: int = 0
    triggers_count: int = 0
    schema_version: str = "1.0"
    metadata_json: str
