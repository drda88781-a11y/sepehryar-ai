"""
Thread-safe SQLite database manager with WAL journal mode and foreign key enforcement.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from app.config.settings import settings
from app.core.logger import get_logger

logger = get_logger("sqlite")


class SQLiteManager:
    """Manages SQLite connections to local app.db."""
    def __init__(self, db_path: Path = settings.sqlite_db_path) -> None:
        self.db_path = db_path

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a contextual connection with WAL mode and row factory."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=10.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        try:
            # Optimize SQLite for concurrency and performance
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute("PRAGMA busy_timeout=5000;")
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"SQLite error: {e}")
            raise
        finally:
            conn.close()


sqlite_manager = SQLiteManager()
