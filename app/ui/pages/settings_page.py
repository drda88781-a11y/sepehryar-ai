"""
Settings Page: Configuration of database defaults, local API ports, and safety options.
"""
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QCheckBox,
    QMessageBox,
)
from app.config.settings import settings
from app.storage.repository import storage_repo


class SettingsPage(QWidget):
    """Settings configuration page."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Container Card
        card = QFrame()
        card.setStyleSheet("background-color: #1A2234; border: 1px solid #26334D; border-radius: 8px; padding: 18px;")
        grid = QGridLayout(card)
        grid.setSpacing(14)

        title = QLabel("تنظیمات کلی سامانه (System Configuration)")
        title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: bold; margin-bottom: 10px;")
        grid.addWidget(title, 0, 0, 1, 2)

        # SQL Server Default
        grid.addWidget(QLabel("سرور SQL پیش‌فرض:"), 1, 0)
        self.input_server = QLineEdit(settings.sql_server)
        grid.addWidget(self.input_server, 1, 1)

        # SQL Database Default
        grid.addWidget(QLabel("نام پایگاه داده پیش‌فرض:"), 2, 0)
        self.input_database = QLineEdit(settings.sql_database)
        grid.addWidget(self.input_database, 2, 1)

        # Local API Port
        grid.addWidget(QLabel("پورت Local API (FastAPI):"), 3, 0)
        self.input_port = QLineEdit(str(settings.api_port))
        grid.addWidget(self.input_port, 3, 1)

        # Offline Strict Mode
        self.chk_offline = QCheckBox("فعال‌سازی حالت سخت‌گیرانه آفلاین (Offline Strict Guard)")
        self.chk_offline.setChecked(settings.offline_strict)
        grid.addWidget(self.chk_offline, 4, 1)

        # Timeout
        grid.addWidget(QLabel("مهلت اجرای کوئری (ثانیه):"), 5, 0)
        self.input_timeout = QLineEdit(str(settings.sql_timeout))
        grid.addWidget(self.input_timeout, 5, 1)

        # SQLite Path
        grid.addWidget(QLabel("مسیر پایگاه داده محلی SQLite:"), 6, 0)
        lbl_sqlite = QLabel(str(settings.sqlite_db_path))
        lbl_sqlite.setStyleSheet("color: #94A3B8; font-family: monospace;")
        grid.addWidget(lbl_sqlite, 6, 1)

        # Save Button
        self.btn_save = QPushButton("💾 ذخیره تنظیمات")
        self.btn_save.setProperty("class", "primary-btn")
        self.btn_save.clicked.connect(self.on_save)
        grid.addWidget(self.btn_save, 7, 1)

        layout.addWidget(card)
        layout.addStretch()

    def on_save(self) -> None:
        """Save settings to local storage."""
        try:
            settings.sql_server = self.input_server.text().strip()
            settings.sql_database = self.input_database.text().strip()
            settings.api_port = int(self.input_port.text().strip())
            settings.offline_strict = self.chk_offline.isChecked()
            settings.sql_timeout = int(self.input_timeout.text().strip())

            storage_repo.set_setting("sql_server", settings.sql_server)
            storage_repo.set_setting("sql_database", settings.sql_database)
            storage_repo.set_setting("api_port", settings.api_port)
            storage_repo.set_setting("offline_strict", settings.offline_strict)

            QMessageBox.information(self, "موفقیت", "تنظیمات سامانه با موفقیت ذخیره شد.")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره تنظیمات: {e}")
