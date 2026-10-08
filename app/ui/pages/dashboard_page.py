"""
Enterprise Dashboard page displaying status badges, quick metric summaries, and action shortcuts.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from app.config.settings import settings
from app.ui.widgets.status_badge import StatusBadge
from app.ui.widgets.metric_card import MetricCard
from app.storage.repository import storage_repo


class DashboardPage(QWidget):
    """Main dashboard page."""

    navigate_requested = Signal(str)  # Emits target page name

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 1. Header Banner
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E293B, stop:1 #0F172A);
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 16px;
            }
        """)
        h_layout = QVBoxLayout(header_card)
        h_title = QLabel("موتور هوش مصنوعی و تحلیل عملیاتی سپهریار (Sepehryar AI Engine)")
        h_title.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: bold;")
        h_sub = QLabel("سامانه کاملاً محلی (Offline-Only) ویژه تحلیل پایگاه داده، عیب‌یابی سرور و دستیار حسابداری سپهریار")
        h_sub.setStyleSheet("color: #94A3B8; font-size: 12px; margin-top: 4px;")
        h_layout.addWidget(h_title)
        h_layout.addWidget(h_sub)
        layout.addWidget(header_card)

        # 2. System Status Badges Row
        badge_layout = QHBoxLayout()
        badge_layout.setSpacing(12)

        self.badge_engine = StatusBadge("موتور هوش مصنوعی", "آنلاین (محلی)", "online")
        self.badge_offline = StatusBadge("حالت شبکه", "۱۰۰٪ آفلاین و امن", "online")
        self.badge_sql = StatusBadge("پایگاه داده SQL", "آماده اتصال", "blue")
        self.badge_llm = StatusBadge("موتور مدل زبانی", "آماده‌سازی فاز ۴", "warning")

        badge_layout.addWidget(self.badge_engine)
        badge_layout.addWidget(self.badge_offline)
        badge_layout.addWidget(self.badge_sql)
        badge_layout.addWidget(self.badge_llm)
        layout.addLayout(badge_layout)

        # 3. Metric Cards Grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(16)

        self.card_tables = MetricCard("تعداد جداول اسکن‌شده", "۰", "در انتظار اولین اسکن", "#0F52BA")
        self.card_active_db = MetricCard("دیتابیس فعال", settings.sql_database, "SQL Server 2019", "#00A86B")
        self.card_audit_count = MetricCard("لاگ‌های مانیتورینگ امنیتی", "۰ رکورد", "عملیات فقط-خواندنی", "#FFBF00")
        self.card_security = MetricCard("حفاظت امنیتی (Safe SQL)", "فعال", "مسدودسازی کامل دستورات مخرب", "#38BDF8")

        grid_layout.addWidget(self.card_tables, 0, 0)
        grid_layout.addWidget(self.card_active_db, 0, 1)
        grid_layout.addWidget(self.card_audit_count, 0, 2)
        grid_layout.addWidget(self.card_security, 0, 3)
        layout.addLayout(grid_layout)

        # 4. Quick Actions Section
        actions_card = QFrame()
        actions_card.setStyleSheet("background-color: #1A2234; border: 1px solid #26334D; border-radius: 8px; padding: 16px;")
        actions_layout = QVBoxLayout(actions_card)
        
        act_title = QLabel("عملیات و ابزارهای سریع")
        act_title.setStyleSheet("color: #F8FAFC; font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        actions_layout.addWidget(act_title)

        btns_row = QHBoxLayout()
        btns_row.setSpacing(12)

        btn_chat = QPushButton("💬 گفت‌وگو با دستیار AI")
        btn_chat.setProperty("class", "primary-btn")
        btn_chat.clicked.connect(lambda: self.navigate_requested.emit("chat"))

        btn_db = QPushButton("🔍 تحلیل و اسکن دیتابیس")
        btn_db.setProperty("class", "secondary-btn")
        btn_db.clicked.connect(lambda: self.navigate_requested.emit("database"))

        btn_query = QPushButton("⚡ Query Explorer")
        btn_query.setProperty("class", "secondary-btn")
        btn_query.clicked.connect(lambda: self.navigate_requested.emit("query"))

        btn_health = QPushButton("🏥 سلامت سیستم")
        btn_health.setProperty("class", "secondary-btn")
        btn_health.clicked.connect(lambda: self.navigate_requested.emit("health"))

        btn_audit = QPushButton("📜 لاگ عملیات")
        btn_audit.setProperty("class", "secondary-btn")
        btn_audit.clicked.connect(lambda: self.navigate_requested.emit("audit"))

        btns_row.addWidget(btn_chat)
        btns_row.addWidget(btn_db)
        btns_row.addWidget(btn_query)
        btns_row.addWidget(btn_health)
        btns_row.addWidget(btn_audit)
        actions_layout.addLayout(btns_row)

        layout.addWidget(actions_card)
        layout.addStretch()

        self.refresh_dashboard_data()

    def refresh_dashboard_data(self) -> None:
        """Update metrics from SQLite repository."""
        scanned = storage_repo.list_scanned_databases()
        if scanned:
            latest = scanned[0]
            self.card_tables.set_value(str(latest["tables_count"]))
            self.card_tables.set_subtitle(f"دیتابیس: {latest['database_name']}")
            self.badge_sql.update_status(f"اسکن شده ({latest['database_name']})", "online")
        
        audits = storage_repo.get_recent_audit_logs(limit=100)
        self.card_audit_count.set_value(f"{len(audits)} رکورد")
