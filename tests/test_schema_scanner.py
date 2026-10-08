"""
Tests for DatabaseScanner, primary keys, foreign keys, and dictionary annotations.
"""
from app.database.mock_provider import get_mock_database_schema
from app.database.scanner import database_scanner


def test_mock_schema_structure():
    """Verify mock schema contains core Sepehryar tables with columns and keys."""
    schema = get_mock_database_schema()
    assert schema.total_tables >= 4
    assert "TblKala" in schema.tables
    assert "TblPerson" in schema.tables
    assert "TR" in schema.tables

    # Check TblKala columns
    kala = schema.tables["TblKala"]
    assert "IDKala" in kala.columns
    assert "NameKala" in kala.columns
    assert "IDKala" in kala.primary_keys
    assert kala.columns["IDKala"].is_identity is True

    # Check Persian dictionary annotations
    assert kala.description is not None
    assert "کالا" in kala.description


def test_relationships_extraction():
    """Verify declared and inferred relationships are captured."""
    schema = get_mock_database_schema()
    assert len(schema.relationships) >= 2

    # Verify TR relationship to TblKala
    tr_kala_rel = next((r for r in schema.relationships if r.target_table == "TblKala"), None)
    assert tr_kala_rel is not None
    assert "IDKala" in tr_kala_rel.source_columns
    assert "IDKala" in tr_kala_rel.target_columns


def test_database_scanner_demo_mode():
    """Verify scanner runs cleanly in offline demo mode and outputs valid schema."""
    schema = database_scanner.scan_database(server="DEMO", database="DEMO", save_to_storage=False)
    assert schema.total_tables >= 4
    assert len(schema.stored_procedures) >= 2
    assert len(schema.views) >= 1
