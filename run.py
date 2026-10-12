"""
Root executable runner for Sepehryar AI Engine.
Supports launching PySide6 Enterprise GUI or executing headless CLI diagnostics and database scans.
"""
import argparse
import sys

# Configure UTF-8 for Windows console outputs
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from app.config.constants import APP_TITLE, APP_TITLE_FA, APP_VERSION
from app.config.settings import settings
from app.core.lifecycle import initialize_application
from app.core.logger import app_logger
from app.database.connection import db_connection_manager
from app.database.mock_provider import get_mock_database_schema
from app.database.scanner import database_scanner
from app.diagnostics.checks import run_full_system_diagnosis
from app.storage.repository import storage_repo


def run_cli_test_connection() -> None:
    """Test connection to SQL Server from CLI."""
    initialize_application()
    print(f"Testing SQL Server connection to {settings.sql_server} / {settings.sql_database}...")
    ok, msg, dbs = db_connection_manager.test_connection()
    if ok:
        print(f"[SUCCESS] {msg}")
        print(f"Available databases: {', '.join(dbs[:10])}...")
    else:
        print(f"[ERROR] {msg}")


def run_cli_scan() -> None:
    """Run database scanner from CLI."""
    initialize_application()
    print(f"Scanning database '{settings.sql_database}' on '{settings.sql_server}'...")
    schema = database_scanner.scan_database()
    print(f"[SUCCESS] Scanned {schema.total_tables} tables, {schema.total_views} views, {schema.total_procs} procedures.")
    print(f"Annotated with Sepehryar dictionary: {schema.dictionary_annotations_count} tables.")


def run_cli_demo() -> None:
    """Load mock database into local SQLite."""
    initialize_application()
    print("Loading offline demo schema for Sepehryar ERP...")
    schema = get_mock_database_schema()
    storage_repo.save_database_metadata(
        database_name=schema.database_name,
        server_name=schema.server_name,
        metadata_dict=schema.model_dump()
    )
    print(f"[SUCCESS] Demo schema '{schema.database_name}' loaded ({schema.total_tables} tables).")


def run_cli_diagnose() -> None:
    """Run system diagnostics from CLI."""
    initialize_application()
    print("Running system and database diagnostics...")
    report = run_full_system_diagnosis()
    print(f"Overall Status: {report.overall_status.value.upper()}")
    for chk in report.checks:
        icon = "[OK]" if chk.status.value == "healthy" else ("[WARN]" if chk.status.value == "warning" else "[FAIL]")
        print(f"{icon} {chk.title}: {chk.value} -> {chk.message}")
        if chk.recommendation:
            print(f"    Recommendation: {chk.recommendation}")


def run_cli_ask(question: str) -> None:
    """Run interactive question through agent orchestrator."""
    initialize_application()
    from app.agent.orchestrator import agent_orchestrator
    print(f"پرسش کاربر: {question}")
    response = agent_orchestrator.process_query(question)
    print("\n--- پاسخ هوش مصنوعی سپهریار ---")
    print(response.persian_answer)
    if response.sql_plan:
        print(f"\nدستور SQL اجرا شده: {response.sql_plan.generated_sql}")
    print(f"مدت‌زمان: {response.duration_ms:.1f} میلی‌ثانیه | قصد: {response.intent.value}")


def main() -> None:
    parser = argparse.ArgumentParser(description=f"{APP_TITLE} ({APP_TITLE_FA}) v{APP_VERSION}")
    parser.add_argument("--test-conn", action="store_true", help="Test connection to configured SQL Server")
    parser.add_argument("--scan", action="store_true", help="Run deep database scan and save metadata")
    parser.add_argument("--demo", action="store_true", help="Load offline Sepehryar demo schema into SQLite")
    parser.add_argument("--diagnose", action="store_true", help="Run system and SQL service health diagnostics")
    parser.add_argument("--ask", type=str, help="Ask a Persian question from Sepehryar AI Agent directly")
    parser.add_argument("--server", "--serve", dest="server", action="store_true", help="Start local REST API server")
    parser.add_argument("--port", type=int, default=settings.api_port, help=f"Port for local REST API (default: {settings.api_port})")
    parser.add_argument("--version", action="store_true", help="Show application version")

    args = parser.parse_args()

    if args.version:
        print(f"{APP_TITLE} ({APP_TITLE_FA}) v{APP_VERSION}")
        return
    elif args.server:
        from app.api.server import start_api_server
        start_api_server(host=settings.api_host, port=args.port)
        return
    elif args.ask:
        run_cli_ask(args.ask)
        return
    elif args.test_conn:
        run_cli_test_connection()
        return
    elif args.scan:
        run_cli_scan()
        return
    elif args.demo:
        run_cli_demo()
        return
    elif args.diagnose:
        run_cli_diagnose()
        return

    # Default: Start PySide6 Graphical User Interface
    from app.main import start_gui
    sys.exit(start_gui())


if __name__ == "__main__":
    main()
