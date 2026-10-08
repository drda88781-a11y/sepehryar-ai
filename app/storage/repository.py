"""
Storage repository providing high-level persistence APIs on SQLite.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from app.core.exceptions import StorageError
from app.core.logger import get_logger
from app.storage.models import (
    CREATE_TABLES_SQL,
    DBConnectionConfig,
    ScannedDatabaseRecord,
)
from app.storage.sqlite import sqlite_manager

logger = get_logger("repository")


class StorageRepository:
    """High-level repository for SQLite operations."""
    def __init__(self, manager=sqlite_manager) -> None:
        self.manager = manager

    def initialize_database(self) -> None:
        """Run DDL migrations to ensure all tables and indexes exist."""
        try:
            with self.manager.get_connection() as conn:
                conn.executescript(CREATE_TABLES_SQL)
            logger.info("SQLite database schema initialized successfully.")
        except Exception as e:
            raise StorageError(
                user_message="ایجاد جداول پایگاه داده محلی با شکست مواجه شد.",
                technical_details=str(e),
                original_exception=e
            )

    # --- Settings ---
    def set_setting(self, key: str, value: Any) -> None:
        """Save a setting value as JSON."""
        val_str = json.dumps(value, ensure_ascii=False)
        now = datetime.now(timezone.utc).isoformat()
        with self.manager.get_connection() as conn:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at;",
                (key, val_str, now)
            )

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Retrieve a setting value."""
        with self.manager.get_connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?;", (key,)).fetchone()
            if row:
                try:
                    return json.loads(row["value"])
                except Exception:
                    return row["value"]
            return default

    # --- Connections ---
    def save_connection(self, config: DBConnectionConfig) -> str:
        """Save or update a database connection configuration."""
        conn_id = config.id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.manager.get_connection() as conn:
            # If set as default, reset other defaults
            if config.is_default:
                conn.execute("UPDATE connections SET is_default = 0;")

            conn.execute(
                """
                INSERT INTO connections (id, name, server, instance, database, auth_type, username, encrypted_password, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    server=excluded.server,
                    instance=excluded.instance,
                    database=excluded.database,
                    auth_type=excluded.auth_type,
                    username=excluded.username,
                    encrypted_password=excluded.encrypted_password,
                    is_default=excluded.is_default,
                    updated_at=excluded.updated_at;
                """,
                (
                    conn_id, config.name, config.server, config.instance, config.database,
                    config.auth_type, config.username, config.encrypted_password,
                    1 if config.is_default else 0,
                    config.created_at or now, now
                )
            )
        return conn_id

    def list_connections(self) -> list[dict[str, Any]]:
        """List all saved connections."""
        with self.manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM connections ORDER BY is_default DESC, name ASC;").fetchall()
            return [dict(r) for r in rows]

    def get_default_connection(self) -> Optional[dict[str, Any]]:
        """Retrieve the default connection configuration."""
        with self.manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM connections WHERE is_default = 1 LIMIT 1;").fetchone()
            if row:
                return dict(row)
            # Fallback to the first connection if no default is explicitly marked
            first = conn.execute("SELECT * FROM connections LIMIT 1;").fetchone()
            return dict(first) if first else None

    # --- Database Metadata Storage ---
    def save_database_metadata(
        self,
        database_name: str,
        server_name: str,
        metadata_dict: dict[str, Any]
    ) -> str:
        """Store or update full scanned metadata for a database in SQLite."""
        meta_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        tables_count = len(metadata_dict.get("tables", {}))
        views_count = len(metadata_dict.get("views", []))
        procs_count = len(metadata_dict.get("stored_procedures", []))
        triggers_count = len(metadata_dict.get("triggers", []))

        json_payload = json.dumps(metadata_dict, ensure_ascii=False)

        with self.manager.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO database_metadata (id, database_name, server_name, scanned_at, tables_count, views_count, procs_count, triggers_count, schema_version, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, '1.0', ?)
                ON CONFLICT(database_name) DO UPDATE SET
                    server_name=excluded.server_name,
                    scanned_at=excluded.scanned_at,
                    tables_count=excluded.tables_count,
                    views_count=excluded.views_count,
                    procs_count=excluded.procs_count,
                    triggers_count=excluded.triggers_count,
                    metadata_json=excluded.metadata_json;
                """,
                (meta_id, database_name, server_name, now, tables_count, views_count, procs_count, triggers_count, json_payload)
            )
        logger.info(f"Saved metadata for database '{database_name}' (tables: {tables_count}, procs: {procs_count})")
        return meta_id

    def get_database_metadata(self, database_name: str) -> Optional[dict[str, Any]]:
        """Retrieve full scanned metadata dictionary for a database."""
        with self.manager.get_connection() as conn:
            row = conn.execute(
                "SELECT metadata_json FROM database_metadata WHERE database_name = ?;",
                (database_name,)
            ).fetchone()
            if row and row["metadata_json"]:
                return json.loads(row["metadata_json"])
            return None

    def list_scanned_databases(self) -> list[dict[str, Any]]:
        """List summary info for all scanned databases."""
        with self.manager.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, database_name, server_name, scanned_at, tables_count, views_count, procs_count, triggers_count
                FROM database_metadata
                ORDER BY scanned_at DESC;
                """
            ).fetchall()
            return [dict(r) for r in rows]

    # --- Audit Logs ---
    def save_audit_record(self, record: Any) -> None:
        """Persist AuditRecord object into SQLite audit_logs table."""
        meta_json = json.dumps(getattr(record, "metadata", {}), ensure_ascii=False)
        with self.manager.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (timestamp, user, action, tool, target_database, sql_query_hash, sql_query_preview, success, duration_ms, error_message, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.timestamp,
                    record.user,
                    record.action,
                    record.tool,
                    record.target_database,
                    record.sql_query_hash,
                    record.sql_query_preview,
                    1 if record.success else 0,
                    record.duration_ms,
                    record.error_message,
                    meta_json
                )
            )

    def get_recent_audit_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch latest audit log entries."""
        with self.manager.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, timestamp, user, action, tool, target_database, sql_query_hash, sql_query_preview, success, duration_ms, error_message
                FROM audit_logs
                ORDER BY id DESC
                LIMIT ?;
                """,
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # --- Tool History ---
    def record_tool_execution(
        self,
        tool_name: str,
        input_data: Any,
        output_data: Any,
        success: bool,
        duration_ms: float
    ) -> None:
        """Log tool invocation history."""
        now = datetime.now(timezone.utc).isoformat()
        in_str = json.dumps(input_data, ensure_ascii=False) if not isinstance(input_data, str) else input_data
        out_str = json.dumps(output_data, ensure_ascii=False) if not isinstance(output_data, str) else output_data

        with self.manager.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO tool_history (timestamp, tool_name, input_json, output_json, success, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (now, tool_name, in_str, out_str, 1 if success else 0, duration_ms)
            )


# Global singleton instance
storage_repo = StorageRepository()
