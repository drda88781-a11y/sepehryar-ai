"""
UI application pages.
"""
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.chat_page import ChatPage
from app.ui.pages.database_page import DatabasePage
from app.ui.pages.health_page import HealthPage
from app.ui.pages.query_page import QueryPage
from app.ui.pages.audit_page import AuditPage
from app.ui.pages.settings_page import SettingsPage

__all__ = [
    "DashboardPage",
    "ChatPage",
    "DatabasePage",
    "HealthPage",
    "QueryPage",
    "AuditPage",
    "SettingsPage",
]
