"""
Main application window for Sepehryar AI Engine (Persian & RTL).
Focuses strictly on:
1. AI Copilot & Architecture Chat
2. Integration Hub for C# migration & report tools
3. Educational Manuals & Knowledge Documents (PDF/Word)
4. Settings
Includes a floating Always-on-top Spotlight Bar.
"""
from PySide6.QtCore import Qt, QKeyCombination
from PySide6.QtGui import QKeySequence, QShortcut
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
from app.ui.pages.chat_page import ChatPage
from app.ui.pages.integration_hub_page import IntegrationHubPage
from app.ui.pages.docs_page import DocsPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.widgets.spotlight_bar import SpotlightBar
from app.ui.theme import APP_STYLESHEET


class MainWindow(QMainWindow):
    """Main window with focused RTL navigation and floating Spotlight bar."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE} | {APP_TITLE_FA} (v{APP_VERSION})")
        self.resize(1260, 780)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(APP_STYLESHEET)

        # Floating Spotlight Bar instance
        self.spotlight_bar = SpotlightBar()

        # Global Shortcut Ctrl+Space to toggle Spotlight Bar
        self.shortcut_spotlight = QShortcut(QKeySequence("Ctrl+Space"), self)
        self.shortcut_spotlight.activated.connect(self._toggle_spotlight)

        self.init_ui()

    def init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Navigation (Right side in RTL)
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("SidebarFrame")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(14, 18, 14, 18)
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
            ("chat", "🧠 کنسول هوش و معمار (AI Copilot)"),
            ("integration", "🔌 مرکز اتصال برنامه‌ها (Integration Hub)"),
            ("docs", "📚 مستندات و جزوات (Knowledge Docs)"),
            ("settings", "⚙️ تنظیمات دیتابیس"),
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
        offline_box.setStyleSheet("background-color: #172033; border: 1px solid #26334D; border-radius: 8px; padding: 10px;")
        ob_layout = QVBoxLayout(offline_box)
        lbl_off_title = QLabel("وضعیت امنیت")
        lbl_off_title.setStyleSheet("color: #94A3B8; font-size: 11px;")
        lbl_off_status = QLabel("● کاملاً آفلاین و محلی")
        lbl_off_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: bold;")
        ob_layout.addWidget(lbl_off_title)
        ob_layout.addWidget(lbl_off_status)
        sidebar_layout.addWidget(offline_box)

        main_layout.addWidget(sidebar_frame)

        # 2. Main Content Area (Header + Pages Stack)
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top Action Bar across content
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #0E131D; border-bottom: 1px solid #1E293B; padding: 8px 16px;")
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(12, 6, 12, 6)

        # Spotlight Bar Button
        btn_spotlight = QPushButton("📌 نوار شناور بالای صفحه (Ctrl+Space)")
        btn_spotlight.setToolTip("باز کردن نوار جستجوی شناور هوش در بالای مانیتور")
        btn_spotlight.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #38BDF8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
                color: #FFFFFF;
            }
        """)
        btn_spotlight.clicked.connect(self._toggle_spotlight)
        tb_layout.addWidget(btn_spotlight)

        tb_layout.addStretch()

        # API Server status badge in top bar
        lbl_api_status = QLabel(f"● سرویس API محلی: آماده (127.0.0.1:{settings.api_port})")
        lbl_api_status.setStyleSheet("color: #34D399; font-size: 11px; font-weight: bold;")
        tb_layout.addWidget(lbl_api_status)

        content_layout.addWidget(top_bar)

        # Pages Stack
        self.pages_stack = QStackedWidget()

        self.page_chat = ChatPage()
        self.page_integration = IntegrationHubPage()
        self.page_docs = DocsPage()
        self.page_settings = SettingsPage()

        self.pages_map = {
            "chat": (0, self.page_chat),
            "integration": (1, self.page_integration),
            "docs": (2, self.page_docs),
            "settings": (3, self.page_settings),
        }

        for pid, (idx, page_widget) in self.pages_map.items():
            self.pages_stack.addWidget(page_widget)

        content_layout.addWidget(self.pages_stack, stretch=1)
        main_layout.addWidget(content_container, stretch=1)

        # 3. Status Bar
        status_bar = QStatusBar()
        status_bar.setStyleSheet("background-color: #0E131D; color: #94A3B8; border-top: 1px solid #1E293B;")
        self.setStatusBar(status_bar)

        self.lbl_status_db = QLabel(f"پایگاه داده: {settings.sql_database}")
        self.lbl_status_srv = QLabel(f"سرور: {settings.sql_server}")
        self.lbl_status_ver = QLabel(f"نسخه: {APP_VERSION}")

        status_bar.addWidget(self.lbl_status_ver)
        status_bar.addPermanentWidget(self.lbl_status_srv)
        status_bar.addPermanentWidget(self.lbl_status_db)

        # Activate initial page
        self.navigate_to("chat")

    def navigate_to(self, page_id: str) -> None:
        """Switch active page and update sidebar button highlights."""
        if page_id not in self.pages_map:
            return

        idx, page_widget = self.pages_map[page_id]
        self.pages_stack.setCurrentIndex(idx)

        for pid, btn in self.nav_buttons.items():
            btn.setChecked(pid == page_id)

        if hasattr(page_widget, "refresh_stats"):
            page_widget.refresh_stats()

    def _toggle_spotlight(self) -> None:
        """Toggle floating spotlight bar on/off."""
        if self.spotlight_bar.isVisible():
            self.spotlight_bar.hide()
        else:
            self.spotlight_bar.show()
            self.spotlight_bar.raise_()
            self.spotlight_bar.activateWindow()
            self.spotlight_bar.input_field.setFocus()
