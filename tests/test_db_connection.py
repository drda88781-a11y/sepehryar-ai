"""
Tests for DBConnectionManager and connection string generation.
"""
from app.database.connection import db_connection_manager


def test_driver_discovery():
    """Verify system driver detection returns a valid ODBC driver."""
    driver = db_connection_manager.get_best_driver()
    assert driver is not None
    assert isinstance(driver, str)
    assert len(driver) > 0


def test_connection_string_builder():
    """Verify connection string formatting for Windows Auth and SQL Auth."""
    win_str = db_connection_manager.build_connection_string(
        server=".\\TEST_SRV",
        database="TestDB",
        auth_type="windows"
    )
    assert "Server=.\\TEST_SRV" in win_str
    assert "Database=TestDB" in win_str
    assert "Trusted_Connection=yes" in win_str

    sql_str = db_connection_manager.build_connection_string(
        server="192.168.1.10",
        database="TestDB",
        auth_type="sql",
        username="sa",
        password="MySecretPassword123"
    )
    assert "UID=sa" in sql_str
    assert "PWD=MySecretPassword123" in sql_str


def test_connection_test_demo_mode():
    """Verify demo connection test succeeds offline."""
    ok, msg, dbs = db_connection_manager.test_connection(server="DEMO", database="DEMO")
    assert ok is True
    assert len(dbs) > 0
