"""
Core configuration package for Sepehryar AI Engine.
"""
from app.config.settings import settings
from app.config.constants import (
    APP_TITLE,
    APP_TITLE_FA,
    APP_VERSION,
    APP_PACKAGE,
    SERVICE_NAME,
    UserRole,
    FORBIDDEN_SQL_KEYWORDS,
    DEFAULT_SQL_TIMEOUT_SEC,
    DEFAULT_SQL_MAX_ROWS,
    DEFAULT_SAMPLE_ROWS_LIMIT,
)

__all__ = [
    "settings",
    "APP_TITLE",
    "APP_TITLE_FA",
    "APP_VERSION",
    "APP_PACKAGE",
    "SERVICE_NAME",
    "UserRole",
    "FORBIDDEN_SQL_KEYWORDS",
    "DEFAULT_SQL_TIMEOUT_SEC",
    "DEFAULT_SQL_MAX_ROWS",
    "DEFAULT_SAMPLE_ROWS_LIMIT",
]
