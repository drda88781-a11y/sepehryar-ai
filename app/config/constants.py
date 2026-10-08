"""
System-wide constants and configurations for Sepehryar AI Engine.
"""
from enum import Enum
from pathlib import Path

APP_TITLE = "Sepehryar AI Engine"
APP_TITLE_FA = "موتور هوش مصنوعی سپهریار"
APP_VERSION = "0.1.0"
APP_PACKAGE = "sepehryar_ai"
SERVICE_NAME = "SepehryarAI"

# Security & Roles
class UserRole(str, Enum):
    VIEWER = "Viewer"
    SUPPORT = "Support"
    SENIOR_SUPPORT = "SeniorSupport"
    ADMIN = "Admin"

# Read-Only Safety enforcement keywords (Forbidden in MVP SQL operations)
FORBIDDEN_SQL_KEYWORDS = frozenset([
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "RENAME",
    "GRANT",
    "REVOKE",
    "DENY",
    "EXEC",
    "EXECUTE",
    "BACKUP",
    "RESTORE",
    "SHUTDOWN",
    "KILL",
    "DBCC",
])

# Default limits
DEFAULT_SQL_TIMEOUT_SEC = 15
DEFAULT_SQL_MAX_ROWS = 100
DEFAULT_SAMPLE_ROWS_LIMIT = 20

# UI Theme & Colors
PRIMARY_COLOR = "#0F52BA"       # Sapphire Blue
ACCENT_COLOR = "#00A86B"        # Jade Green (Healthy)
WARNING_COLOR = "#FFBF00"       # Amber
DANGER_COLOR = "#E63946"        # Coral Red
BG_DARK = "#121824"
SURFACE_DARK = "#1A2234"
TEXT_LIGHT = "#E2E8F0"
TEXT_MUTED = "#94A3B8"

# Persian UI Text strings
TEXT_ONLINE = "آنلاین (محلی)"
TEXT_OFFLINE = "آفلاین"
TEXT_CONNECTED = "متصل"
TEXT_DISCONNECTED = "قطع ارتباط"
TEXT_READY = "آماده به‌کار"
TEXT_SCANNING = "در حال تحلیل و اسکن..."
TEXT_SUCCESS = "عملیات با موفقیت انجام شد"
