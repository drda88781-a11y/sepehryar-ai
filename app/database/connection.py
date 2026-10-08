"""
SQL Server Connection Manager utilizing pyodbc with automated driver selection,
dual-authentication support (Windows Auth & SQL Auth), and connection testing.
"""
from contextlib import contextmanager
from typing import Optional, Generator, Any
import pyodbc
from app.config.settings import settings
from app.core.exceptions import DatabaseConnectionError
from app.core.logger import get_logger, scrub_credentials
from app.core.security import decrypt_credential

logger = get_logger("connection")


class DBConnectionManager:
    """Manages connections to SQL Server instances."""

    def __init__(self) -> None:
        self.cached_driver: Optional[str] = None

    def get_best_driver(self) -> str:
        """Find the most modern SQL Server ODBC driver installed on the Windows host."""
        if self.cached_driver:
            return self.cached_driver
        available = pyodbc.drivers()
        # Priority list
        preferred = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server",
        ]
        for driver in preferred:
            if driver in available:
                self.cached_driver = driver
                logger.debug(f"Selected ODBC Driver: {driver}")
                return driver
        # Fallback to whatever first driver contains SQL
        for d in available:
            if "sql" in d.lower():
                self.cached_driver = d
                return d
        return "SQL Server"

    def build_connection_string(
        self,
        server: Optional[str] = None,
        database: Optional[str] = None,
        auth_type: str = "windows",
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> str:
        """Construct a secure pyodbc connection string."""
        driver = self.get_best_driver()
        srv = server or settings.sql_server
        db = database or settings.sql_database
        to = timeout or settings.sql_timeout

        parts = [
            f"Driver={{{driver}}}",
            f"Server={srv}",
            "TrustServerCertificate=yes",
            f"Connection Timeout={to}",
        ]

        if db:
            parts.append(f"Database={db}")

        if auth_type.lower() == "windows":
            parts.append("Trusted_Connection=yes")
        else:
            usr = username or settings.sql_username
            pwd = password or settings.sql_password
            # In case password was stored encrypted
            pwd_decrypted = decrypt_credential(pwd) if pwd else ""
            parts.append(f"UID={usr}")
            parts.append(f"PWD={pwd_decrypted}")

        return ";".join(parts) + ";"

    def test_connection(
        self,
        server: Optional[str] = None,
        database: Optional[str] = None,
        auth_type: str = "windows",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> tuple[bool, str, list[str]]:
        """
        Verify connection to SQL Server and list available databases.
        Returns: (success: bool, status_message: str, database_names: list[str])
        """
        # Check if Demo / Mock mode is explicitly requested
        target_srv = (server or settings.sql_server).strip()
        target_db = (database or settings.sql_database or "").strip()
        if target_srv.upper() in ("DEMO", "MOCK", "OFFLINE_DEMO"):
            return True, "اتصال به پایگاه داده دمو سپهریار (آفلاین) برقرار شد.", ["Sepehr_hesabico_1403", "Sepehr_Main_Demo"]

        conn_str = self.build_connection_string(
            server=target_srv,
            database=target_db if target_db else "master",
            auth_type=auth_type,
            username=username,
            password=password,
            timeout=5
        )

        try:
            logger.info(f"Testing SQL connection to server: {target_srv}...")
            with pyodbc.connect(conn_str, timeout=settings.sql_timeout) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sys.databases WHERE state_desc = 'ONLINE' ORDER BY name;")
                rows = cursor.fetchall()
                db_names = [r[0] for r in rows if r[0] not in ('tempdb', 'model', 'msdb')]
                return True, f"اتصال به سرور {target_srv} با موفقیت برقرار شد. تعداد {len(db_names)} پایگاه داده در دسترس است.", db_names
        except Exception as e:
            err_msg = str(e)
            logger.error(f"SQL Connection test failed: {scrub_credentials(err_msg)}")
            # Persian user-friendly explanation
            fa_error = "امکان برقراری ارتباط با SQL Server وجود ندارد."
            if "Login failed" in err_msg:
                fa_error = "نام کاربری یا کلمه عبور وارد شده برای SQL Server صحیح نیست."
            elif "does not exist or access denied" in err_msg or "SQL Server does not exist" in err_msg:
                fa_error = f"سرور '{target_srv}' یافت نشد. لطفاً از روشن بودن سرویس SQL Server و نام Instance اطمینان حاصل کنید."
            elif "Cannot open database" in err_msg:
                fa_error = f"دیتابیس '{target_db}' در سرور یافت نشد یا کاربر دسترسی لازم را ندارد."

            return False, fa_error, []

    @contextmanager
    def get_connection(
        self,
        server: Optional[str] = None,
        database: Optional[str] = None,
        auth_type: str = "windows",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Generator[pyodbc.Connection, None, None]:
        """Context manager yielding active pyodbc connection."""
        conn_str = self.build_connection_string(
            server=server,
            database=database,
            auth_type=auth_type,
            username=username,
            password=password
        )
        try:
            conn = pyodbc.connect(conn_str, timeout=settings.sql_timeout)
            try:
                yield conn
            finally:
                conn.close()
        except Exception as e:
            raise DatabaseConnectionError(
                user_message="خطا در ارتباط با دیتابیس رخ داد.",
                technical_details=scrub_credentials(str(e)),
                original_exception=e
            )


# Global singleton instance
db_connection_manager = DBConnectionManager()
