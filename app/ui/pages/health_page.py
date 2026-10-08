"""
Health Center Page: Displays CPU, RAM, Disk space, and SQL Server service health status.
"""
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
)
from app.diagnostics.checks import run_full_system_diagnosis, SystemHealthStatus


class HealthPage(QWidget):
    """System and Database Health Center."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header bar
        header_bar = QHBoxLayout()
        title = QLabel("مرکز پایش سلامت سیستم و سرویس‌های سپهریار (Health Center)")
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold;")
        header_bar.addWidget(title)
        header_bar.addStretch()

        self.btn_refresh = QPushButton("🔄 عیب‌یابی مجدد سیستم")
        self.btn_refresh.setProperty("class", "primary-btn")
        self.btn_refresh.clicked.connect(self.run_diagnosis)
        header_bar.addWidget(self.btn_refresh)
        layout.addLayout(header_bar)

        # Overall Banner
        self.banner = QFrame()
        self.banner_layout = QVBoxLayout(self.banner)
        self.lbl_overall = QLabel("در حال ارزیابی وضعیت...")
        self.lbl_overall.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.banner_layout.addWidget(self.lbl_overall)
        layout.addWidget(self.banner)

        # Scroll Area for check cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(12)
        scroll.setWidget(self.cards_container)

        layout.addWidget(scroll)
        self.run_diagnosis()

    def run_diagnosis(self) -> None:
        """Execute full diagnostics and populate cards."""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        report = run_full_system_diagnosis()

        # Update banner
        if report.overall_status == SystemHealthStatus.HEALTHY:
            self.banner.setStyleSheet("background-color: #064E3B; border: 1px solid #059669; border-radius: 8px; padding: 12px;")
            self.lbl_overall.setStyleSheet("color: #34D399; font-weight: bold;")
            self.lbl_overall.setText("✅ کلیه مؤلفه‌های سیستمی، منابع سخت‌افزاری و اتصالات پایگاه داده در وضعیت سالم و پایدار هستند.")
        elif report.overall_status == SystemHealthStatus.WARNING:
            self.banner.setStyleSheet("background-color: #78350F; border: 1px solid #D97706; border-radius: 8px; padding: 12px;")
            self.lbl_overall.setStyleSheet("color: #FBBF24; font-weight: bold;")
            self.lbl_overall.setText(f"⚠️ توجه: {report.warnings_count} هشدار سیستمی شناسایی شد. لطفاً توصیه‌های ذیل را بررسی نمایید.")
        else:
            self.banner.setStyleSheet("background-color: #7F1D1D; border: 1px solid #DC2626; border-radius: 8px; padding: 12px;")
            self.lbl_overall.setStyleSheet("color: #F87171; font-weight: bold;")
            self.lbl_overall.setText(f"❌ خطای بحرانی: {report.critical_count} مشکل سیستمی عملکرد سامانه را مختل کرده است.")

        # Create check cards
        for chk in report.checks:
            card = QFrame()
            card.setStyleSheet("background-color: #1A2234; border: 1px solid #26334D; border-radius: 8px; padding: 12px;")
            c_layout = QVBoxLayout(card)
            c_layout.setSpacing(6)

            top_row = QHBoxLayout()
            c_title = QLabel(chk.title)
            c_title.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold;")

            c_val = QLabel(chk.value)
            color = "#00A86B" if chk.status == SystemHealthStatus.HEALTHY else ("#FFBF00" if chk.status == SystemHealthStatus.WARNING else "#E63946")
            c_val.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")

            top_row.addWidget(c_title)
            top_row.addStretch()
            top_row.addWidget(c_val)
            c_layout.addLayout(top_row)

            c_msg = QLabel(chk.message)
            c_msg.setStyleSheet("color: #94A3B8; font-size: 12px;")
            c_layout.addWidget(c_msg)

            if chk.recommendation:
                c_rec = QLabel(f"💡 اقدام پیشنهادی: {chk.recommendation}")
                c_rec.setStyleSheet("color: #38BDF8; font-size: 12px; font-weight: bold; margin-top: 4px;")
                c_layout.addWidget(c_rec)

            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()
