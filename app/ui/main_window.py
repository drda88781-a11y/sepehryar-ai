"""
Main application window for Sepehryar AI Engine (Persian & RTL).
Provides navigation between Dashboard, Database Analysis, Query Explorer, Health, and Settings.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
    QLabel,
    QFrame,
    QStatusBar,
)
from app.config.constants import APP_TITLE, APP_TITLE_FA, APP_VERSION
from app.config.settings import settings
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.chat_page import ChatPage
from app.ui.pages.database_page import DatabasePage
from app.ui.pages.health_page import HealthPage
from app.ui.pages.query_page import QueryPage
from app.ui.pages.audit_page import AuditPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.theme import APP_STYLESHEET


class MainWindow(QMainWindow):
    """Main window with RTL sidebar navigation."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE} | {APP_TITLE_FA} (v{APP_VERSION})")
        self.resize(1280, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(APP_STYLESHEET)

        self.init_ui()

    def init_ui(self) -> None:
        # Central Container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Navigation (Right side in RTL)
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("SidebarFrame")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(8)

        # App Brand Header
        app_title = QLabel(APP_TITLE_FA)
        app_title.setObjectName("SidebarTitle")
        app_sub = QLabel("موتور هوش مصنوعی و پایگاه داده")
        app_sub.setObjectName("SidebarSubtitle")
        sidebar_layout.addWidget(app_title)
        sidebar_layout.addWidget(app_sub)

        # Nav Buttons
        self.nav_buttons: dict[str, QPushButton] = {}
        pages_config = [
            ("dashboard", "📊 داشبورد"),
            ("chat", "💬 گفت‌وگو با AI"),
            ("database", "🔍 تحلیل دیتابیس"),
            ("query", "⚡ Query Explorer"),
            ("health", "🏥 سلامت سیستم"),
            ("audit", "📜 لاگ عملیات"),
            ("settings", "⚙️ تنظیمات"),
        ]

        for page_id, label in pages_config:
            btn = QPushButton(label)
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, pid=page_id: self.navigate_to(pid))
            self.nav_buttons[page_id] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Offline indicator at sidebar bottom
        offline_box = QFrame()
        offline_box.setStyleSheet("background-color: #1A2234; border: 1px solid #26334D; border-radius: 6px; padding: 8px;")
        ob_layout = QVBoxLayout(offline_box)
        lbl_off_title = QLabel("وضعیت امنیت")
        lbl_off_title.setStyleSheet("color: #94A3B8; font-size: 11px;")
        lbl_off_status = QLabel("● کاملاً آفلاین و محلی")
        lbl_off_status.setStyleSheet("color: #00A86B; font-size: 11px; font-weight: bold;")
        ob_layout.addWidget(lbl_off_title)
        ob_layout.addWidget(lbl_off_status)
        sidebar_layout.addWidget(offline_box)

        main_layout.addWidget(sidebar_frame)

        # 2. Main Pages Stack
        self.pages_stack = QStackedWidget()

        self.page_dashboard = DashboardPage()
        self.page_dashboard.navigate_requested.connect(self.navigate_to)
        self.page_chat = ChatPage()
        self.page_database = DatabasePage()
        self.page_query = QueryPage()
        self.page_health = HealthPage()
        self.page_audit = AuditPage()
        self.page_settings = SettingsPage()

        self.pages_map = {
            "dashboard": (0, self.page_dashboard),
            "chat": (1, self.page_chat),
            "database": (2, self.page_database),
            "query": (3, self.page_query),
            "health": (4, self.page_health),
            "audit": (5, self.page_audit),
            "settings": (6, self.page_settings),
        }

        for pid, (idx, page_widget) in self.pages_map.items():
            self.pages_stack.addWidget(page_widget)

        main_layout.addWidget(self.pages_stack)

        # 3. Status Bar
        status_bar = QStatusBar()
        status_bar.setStyleSheet("background-color: #0E131D; color: #94A3B8; border-top: 1px solid #1E293B;")
        self.setStatusBar(status_bar)

        self.lbl_status_db = QLabel(f"پایگاه داده هدف: {settings.sql_database}")
        self.lbl_status_srv = QLabel(f"سرور: {settings.sql_server}")
        self.lbl_status_ver = QLabel(f"نسخه: {APP_VERSION}")

        status_bar.addWidget(self.lbl_status_ver)
        status_bar.addPermanentWidget(self.lbl_status_srv)
        status_bar.addPermanentWidget(self.lbl_status_db)

        # Activate initial page
        self.navigate_to("dashboard")

    def navigate_to(self, page_id: str) -> None:
        """Switch active page and update sidebar button highlights."""
        if page_id not in self.pages_map:
            return

        idx, page_widget = self.pages_map[page_id]
        self.pages_stack.setCurrentIndex(idx)

        for pid, btn in self.nav_buttons.items():
            btn.setChecked(pid == page_id)

        # Refresh page data if applicable
        if hasattr(page_widget, "refresh_dashboard_data"):
            page_widget.refresh_dashboard_data()
        elif hasattr(page_widget, "load_audit_logs"):
            page_widget.load_audit_logs()
