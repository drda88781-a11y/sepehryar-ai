"""
Deep SQL Server Database Scanner: extracts tables, columns, constraints,
indexes, triggers, views, stored procedures, and relationships.
"""
import time
from datetime import datetime, timezone
from typing import Optional, Any
from app.config.settings import settings
from app.core.audit import record_audit
from app.core.exceptions import DatabaseScanError
from app.core.logger import get_logger
from app.database.connection import db_connection_manager
from app.database.metadata import (
    DatabaseSchema,
    TableMetadata,
    ColumnMetadata,
    ConstraintMetadata,
    IndexMetadata,
    TriggerMetadata,
    StoredProcMetadata,
    ViewMetadata,
    SEPEHRYAR_TABLE_DICTIONARY,
    SEPEHRYAR_COLUMN_DICTIONARY,
)
from app.database.mock_provider import get_mock_database_schema
from app.database.relationships import (
    extract_declared_relationships,
    infer_relationships_heuristically,
)
from app.storage.repository import storage_repo

logger = get_logger("scanner")


class DatabaseScanner:
    """Performs deep introspection of SQL Server databases without locking production tables."""

    def __init__(self, connection_manager=db_connection_manager) -> None:
        self.conn_mgr = connection_manager

    def scan_database(
        self,
        server: Optional[str] = None,
        database: Optional[str] = None,
        auth_type: str = "windows",
        username: Optional[str] = None,
        password: Optional[str] = None,
        save_to_storage: bool = True,
    ) -> DatabaseSchema:
        """Scan target database and optionally persist metadata to SQLite."""
        target_server = server or settings.sql_server
        target_db = database or settings.sql_database

        start_time = time.perf_counter()
        logger.info(f"Initiating deep scan for database '{target_db}' on '{target_server}'...")

        # If offline demo requested
        if target_server.upper() in ("DEMO", "MOCK", "OFFLINE_DEMO") or target_db.upper() in ("DEMO", "MOCK"):
            schema = get_mock_database_schema(target_db)
            if save_to_storage:
                storage_repo.save_database_metadata(
                    database_name=schema.database_name,
                    server_name=schema.server_name,
                    metadata_dict=schema.model_dump()
                )
            record_audit(
                action="DATABASE_SCAN",
                tool="database_scanner",
                target_database=target_db,
                success=True,
                duration_ms=(time.perf_counter() - start_time) * 1000,
                metadata={"mode": "demo_mock", "tables_count": schema.total_tables}
            )
            return schema

        try:
            with self.conn_mgr.get_connection(
                server=target_server,
                database=target_db,
                auth_type=auth_type,
                username=username,
                password=password
            ) as conn:
                schema = self._introspect_sql_server(conn, target_server, target_db)

            # Persist to local SQLite repository
            if save_to_storage:
                storage_repo.save_database_metadata(
                    database_name=schema.database_name,
                    server_name=schema.server_name,
                    metadata_dict=schema.model_dump()
                )

            duration = (time.perf_counter() - start_time) * 1000
            record_audit(
                action="DATABASE_SCAN",
                tool="database_scanner",
                target_database=target_db,
                success=True,
                duration_ms=duration,
                metadata={
                    "tables": schema.total_tables,
                    "views": schema.total_views,
                    "procs": schema.total_procs,
                    "triggers": schema.total_triggers,
                }
            )
            logger.info(
                f"Scan of '{target_db}' completed in {duration:.1f}ms: "
                f"{schema.total_tables} tables, {schema.total_views} views, {schema.total_procs} procs."
            )
            return schema

        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            record_audit(
                action="DATABASE_SCAN",
                tool="database_scanner",
                target_database=target_db,
                success=False,
                duration_ms=duration,
                error_message=str(e)
            )
            logger.error(f"Scan failed for database '{target_db}': {e}")
            raise DatabaseScanError(
                user_message=f"اسکن متادیتای پایگاه داده '{target_db}' با شکست مواجه شد.",
                technical_details=str(e),
                original_exception=e
            )

    def _introspect_sql_server(self, conn: Any, server: str, db: str) -> DatabaseSchema:
        """Run metadata extraction queries on SQL Server catalog views."""
        schema = DatabaseSchema(
            database_name=db,
            server_name=server,
            scanned_at=datetime.now(timezone.utc).isoformat()
        )
        cursor = conn.cursor()

        # 1. Tables & Row Counts (Non-locking partition statistics)
        tables_query = """
        SELECT 
            t.object_id,
            s.name AS schema_name,
            t.name AS table_name,
            t.create_date,
            t.modify_date,
            ISNULL(SUM(p.rows), 0) AS row_count
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        LEFT JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0, 1)
        WHERE t.is_ms_shipped = 0
        GROUP BY t.object_id, s.name, t.name, t.create_date, t.modify_date
        ORDER BY t.name;
        """
        cursor.execute(tables_query)
        table_id_map: dict[int, str] = {}
        for row in cursor.fetchall():
            tbl_name = row.table_name
            table_id_map[row.object_id] = tbl_name
            desc = SEPEHRYAR_TABLE_DICTIONARY.get(tbl_name)

            table_meta = TableMetadata(
                name=tbl_name,
                schema_name=row.schema_name,
                row_count=int(row.row_count),
                created_date=row.create_date.isoformat() if row.create_date else None,
                modified_date=row.modify_date.isoformat() if row.modify_date else None,
                description=desc
            )
            schema.tables[tbl_name] = table_meta

        # 2. Columns
        columns_query = """
        SELECT 
            c.object_id,
            c.name AS column_name,
            tp.name AS data_type,
            c.max_length,
            c.precision,
            c.scale,
            c.is_nullable,
            c.is_identity,
            c.is_computed,
            c.column_id AS ordinal_position,
            OBJECT_DEFINITION(c.default_object_id) AS default_value
        FROM sys.columns c
        INNER JOIN sys.types tp ON c.user_type_id = tp.user_type_id
        WHERE c.object_id IN (SELECT object_id FROM sys.tables WHERE is_ms_shipped = 0)
        ORDER BY c.object_id, c.column_id;
        """
        cursor.execute(columns_query)
        for row in cursor.fetchall():
            tbl_name = table_id_map.get(row.object_id)
            if not tbl_name or tbl_name not in schema.tables:
                continue

            col_desc = SEPEHRYAR_COLUMN_DICTIONARY.get(row.column_name)
            col_meta = ColumnMetadata(
                name=row.column_name,
                data_type=row.data_type,
                max_length=row.max_length,
                precision=row.precision,
                scale=row.scale,
                is_nullable=bool(row.is_nullable),
                is_identity=bool(row.is_identity),
                is_computed=bool(row.is_computed),
                default_value=row.default_value,
                ordinal_position=row.ordinal_position,
                description=col_desc
            )
            schema.tables[tbl_name].columns[row.column_name] = col_meta

        # 3. Primary Keys
        pk_query = """
        SELECT 
            kc.parent_object_id AS object_id,
            kc.name AS pk_name,
            c.name AS column_name
        FROM sys.key_constraints kc
        INNER JOIN sys.index_columns ic ON kc.parent_object_id = ic.object_id AND kc.unique_index_id = ic.index_id
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE kc.type = 'PK';
        """
        cursor.execute(pk_query)
        for row in cursor.fetchall():
            tbl_name = table_id_map.get(row.object_id)
            if tbl_name and tbl_name in schema.tables:
                schema.tables[tbl_name].primary_keys.append(row.column_name)

        # 4. Indexes
        idx_query = """
        SELECT 
            i.object_id,
            i.name AS index_name,
            i.is_unique,
            i.is_primary_key,
            c.name AS column_name
        FROM sys.indexes i
        INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE i.object_id IN (SELECT object_id FROM sys.tables WHERE is_ms_shipped = 0)
          AND i.name IS NOT NULL
        ORDER BY i.object_id, i.name, ic.key_ordinal;
        """
        cursor.execute(idx_query)
        idx_acc: dict[tuple[str, str], IndexMetadata] = {}
        for row in cursor.fetchall():
            tbl_name = table_id_map.get(row.object_id)
            if not tbl_name or tbl_name not in schema.tables:
                continue
            key = (tbl_name, row.index_name)
            if key not in idx_acc:
                idx_acc[key] = IndexMetadata(
                    name=row.index_name,
                    is_unique=bool(row.is_unique),
                    is_primary=bool(row.is_primary_key),
                    columns=[row.column_name]
                )
            else:
                idx_acc[key].columns.append(row.column_name)

        for (tbl_name, _), idx_meta in idx_acc.items():
            schema.tables[tbl_name].indexes.append(idx_meta)

        # 5. Triggers
        trg_query = """
        SELECT 
            t.parent_id AS object_id,
            t.name AS trigger_name,
            t.is_disabled,
            t.is_instead_of_trigger
        FROM sys.triggers t
        WHERE t.parent_id IN (SELECT object_id FROM sys.tables WHERE is_ms_shipped = 0);
        """
        cursor.execute(trg_query)
        for row in cursor.fetchall():
            tbl_name = table_id_map.get(row.object_id)
            if not tbl_name or tbl_name not in schema.tables:
                continue
            trg_meta = TriggerMetadata(
                name=row.trigger_name,
                table_name=tbl_name,
                is_disabled=bool(row.is_disabled),
                is_instead_of=bool(row.is_instead_of_trigger)
            )
            schema.tables[tbl_name].triggers.append(trg_meta)
            schema.triggers.append(trg_meta)

        # 6. Views
        views_query = "SELECT name, SCHEMA_NAME(schema_id) AS schema_name FROM sys.views WHERE is_ms_shipped = 0 ORDER BY name;"
        cursor.execute(views_query)
        for row in cursor.fetchall():
            schema.views.append(ViewMetadata(name=row.name, schema_name=row.schema_name))

        # 7. Stored Procedures
        procs_query = "SELECT name, SCHEMA_NAME(schema_id) AS schema_name FROM sys.procedures WHERE is_ms_shipped = 0 ORDER BY name;"
        cursor.execute(procs_query)
        for row in cursor.fetchall():
            schema.stored_procedures.append(StoredProcMetadata(name=row.name, schema_name=row.schema_name))

        # 8. Declared & Inferred Relationships
        declared_rels = extract_declared_relationships(conn)
        inferred_rels = infer_relationships_heuristically(schema.tables, declared_rels)
        schema.relationships = declared_rels + inferred_rels

        # Annotations count
        schema.dictionary_annotations_count = sum(1 for t in schema.tables.values() if t.description)

        return schema


database_scanner = DatabaseScanner()
