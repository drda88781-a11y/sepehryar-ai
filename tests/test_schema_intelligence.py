"""
Comprehensive tests for Schema Intelligence Core:
- SchemaKnowledgeGraph (Table Cards & BFS Join Path generation)
- MigrationRulesEngine (Polarity, Person Cleaning, Balance Validation)
- DatabaseProvisioner (Index Scripting & Transactional Opening Voucher)
- REST API Endpoints for external applications
"""
from fastapi.testclient import TestClient
from app.api.server import create_api_app
from app.database.schema_graph import schema_graph
from app.database.migration_rules import migration_engine
from app.database.provisioner import database_provisioner
from app.config.settings import settings

app = create_api_app()
client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {settings.api_token}"}


def test_schema_graph_tables_and_cards():
    """Verify all core ERP tables are cataloged with primary keys and notes."""
    tables = schema_graph.list_all_tables()
    names = {t["table_name"] for t in tables}
    assert "Master" in names
    assert "TR" in names
    assert "TblPerson" in names
    assert "TblKala" in names
    assert "TblHesabText" in names

    card_master = schema_graph.get_table_card("Master")
    assert card_master is not None
    assert "Srfsl" in card_master.primary_keys
    assert "personcod" in card_master.vital_columns


def test_schema_graph_join_paths():
    """Verify BFS finds shortest valid paths between decoupled tables."""
    # Person -> Kala (via TR)
    path_pk = schema_graph.find_join_path("TblPerson", "TblKala")
    assert path_pk is not None
    assert len(path_pk) == 2
    assert path_pk[0].target_table == "TR"
    assert path_pk[1].target_table == "TblKala"

    # Master -> TblSanad (via TR)
    path_ms = schema_graph.find_join_path("Master", "TblSanad")
    assert path_ms is not None
    assert len(path_ms) == 2

    # Direct relation: Master -> TblPerson
    path_direct = schema_graph.find_join_path("Master", "TblPerson")
    assert path_direct is not None
    assert len(path_direct) == 1
    assert "personcod = TblPerson.Sh_ozviat" in path_direct[0].join_condition


def test_schema_graph_report_query_builder():
    """Verify dynamic report query generation without Cartesian products."""
    sql = schema_graph.build_joined_report_query(
        tables=["TblPerson", "TR", "TblKala"],
        select_fields=["p.Name", "k.Name AS Kala", "tr.TED"],
        where_clauses=["p.Type = 1"],
        order_by="tr.TED DESC",
        top_limit=25
    )
    assert "SELECT TOP (25)" in sql
    assert "FROM dbo.TblPerson WITH (NOLOCK)" in sql
    assert "LEFT JOIN dbo.TR WITH (NOLOCK)" in sql
    assert "LEFT JOIN dbo.TblKala WITH (NOLOCK)" in sql
    assert "ORDER BY tr.TED DESC" in sql


def test_migration_engine_polarity_resolution():
    """Verify signed and unsigned balance conversion to atomic (Bed, Bes)."""
    # Standard signed
    bed1, bes1 = migration_engine.resolve_polarity("Standard", balance=5000000)
    assert bed1 == 5000000 and bes1 == 0

    bed2, bes2 = migration_engine.resolve_polarity("Standard", balance=-3000000)
    assert bed2 == 0 and bes2 == 3000000

    # Baran 360: RemainAccount < 0 is Debtor
    bed_baran, bes_baran = migration_engine.resolve_polarity("Baran360", balance=-4500000)
    assert bed_baran == 4500000 and bes_baran == 0


def test_migration_engine_person_cleaning():
    """Verify phone separation from person names and Type assignment."""
    res = migration_engine.clean_person_fields(
        raw_name="علی فکوری 09138548850",
        raw_tell="03538221100",
        is_bank=False
    )
    assert res.clean_name == "علی فکوری"
    assert res.mobile == "09138548850"
    assert res.tell == "03538221100"
    assert res.type_code == 1

    # Bank cleaning
    res_bank = migration_engine.clean_person_fields(raw_name="بانک صادرات مرکزی", is_bank=True)
    assert res_bank.type_code == 4
    assert res_bank.srfsl_code == 100
    assert res_bank.moin_code == 2


def test_migration_engine_balance_validation():
    """Verify opening balance sum equality check."""
    balanced_records = [
        {"Bed": 1000000, "Bes": 0},
        {"Bed": 0, "Bes": 1000000},
    ]
    rep = migration_engine.validate_opening_balance(balanced_records)
    assert rep.is_valid is True
    assert rep.difference == 0

    unbalanced_records = [
        {"Bed": 1000000, "Bes": 0},
        {"Bed": 0, "Bes": 800000},
    ]
    rep_bad = migration_engine.validate_opening_balance(unbalanced_records)
    assert rep_bad.is_valid is False
    assert rep_bad.difference == 200000


def test_provisioner_scripts_generation():
    """Verify generation of indexing DDL and opening voucher SQL."""
    ddl = database_provisioner.generate_tuning_script()
    assert "IX_TR_Factor_Sodor" in ddl
    assert "IX_Master_personcod" in ddl

    voucher_sql = database_provisioner.generate_opening_voucher_transaction_sql(
        sanad_number=1,
        date_shamsi="1405/01/01",
        articles=[{"Sodor": 1, "Srfsl": 110, "Moin": 1, "HSB": 10, "Bed": 1000, "Bes": 0}]
    )
    assert "BEGIN TRANSACTION" in voucher_sql
    assert "DISABLE TRIGGER dbo.UpdateSiteSync_TR" in voucher_sql
    assert "ENABLE TRIGGER dbo.UpdateSiteSync_TR" in voucher_sql


def test_api_schema_intelligence_endpoints():
    """Verify REST endpoints for external applications."""
    # List tables
    res_tables = client.get("/api/schema/tables", headers=AUTH_HEADERS)
    assert res_tables.status_code == 200
    assert len(res_tables.json()["tables"]) > 0

    # Join path endpoint
    res_path = client.post(
        "/api/schema/join-path",
        headers=AUTH_HEADERS,
        json={"source_table": "TblPerson", "target_table": "TblKala"}
    )
    assert res_path.status_code == 200
    data = res_path.json()
    assert data["path_length"] == 2

    # Clean person endpoint
    res_clean = client.post(
        "/api/schema/clean-person",
        headers=AUTH_HEADERS,
        json={"name": "حسین محمودیان 09134537853"}
    )
    assert res_clean.status_code == 200
    assert res_clean.json()["clean_name"] == "حسین محمودیان"
    assert res_clean.json()["mobile"] == "09134537853"

    # Validate migration endpoint
    res_val = client.post(
        "/api/schema/validate-migration",
        headers=AUTH_HEADERS,
        json={"records": [{"Bed": 500, "Bes": 500}]}
    )
    assert res_val.status_code == 200
    assert res_val.json()["is_valid"] is True
