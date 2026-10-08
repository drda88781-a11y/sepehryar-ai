"""
Tests for local SQLite repository and metadata storage.
"""
from app.core.audit import AuditRecord
from app.storage.models import DBConnectionConfig
from app.storage.repository import storage_repo


def test_sqlite_settings_crud():
    """Verify settings save and retrieval in SQLite."""
    storage_repo.set_setting("test_key", {"theme": "dark", "zoom": 1.2})
    val = storage_repo.get_setting("test_key")
    assert isinstance(val, dict)
    assert val["theme"] == "dark"
    assert val["zoom"] == 1.2


def test_sqlite_connection_management():
    """Verify storing, updating, and querying SQL Server connections."""
    conn_cfg = DBConnectionConfig(
        name="MainAccountingTest",
        server=".\\SEPEHRYAR2019",
        database="Sepehr_hesabico_1403",
        auth_type="windows",
        is_default=True
    )
    conn_id = storage_repo.save_connection(conn_cfg)
    assert conn_id is not None

    connections = storage_repo.list_connections()
    assert any(c["name"] == "MainAccountingTest" for c in connections)

    default_conn = storage_repo.get_default_connection()
    assert default_conn is not None
    assert default_conn["name"] == "MainAccountingTest"


def test_sqlite_database_metadata_storage():
    """Verify persisting full database metadata schema into SQLite."""
    from app.database.mock_provider import get_mock_database_schema
    schema = get_mock_database_schema(db_name="TestDB_1403")
    meta_payload = schema.model_dump()
    meta_id = storage_repo.save_database_metadata(
        database_name="TestDB_1403",
        server_name=".\\TEST_SRV",
        metadata_dict=meta_payload
    )
    assert meta_id is not None

    retrieved = storage_repo.get_database_metadata("TestDB_1403")
    assert retrieved is not None
    assert "TblKala" in retrieved["tables"]
    assert len(retrieved["views"]) == 2

    all_dbs = storage_repo.list_scanned_databases()
    assert any(d["database_name"] == "TestDB_1403" for d in all_dbs)


def test_sqlite_audit_logs():
    """Verify persisting audit records into SQLite."""
    rec = AuditRecord(
        user="test_auditor",
        action="TEST_ACTION",
        tool="test_tool",
        target_database="TestDB_1403",
        success=True,
        duration_ms=45.2
    )
    storage_repo.save_audit_record(rec)
    logs = storage_repo.get_recent_audit_logs(limit=10)
    assert len(logs) > 0
    assert any(l["action"] == "TEST_ACTION" for l in logs)
