"""
Audit Logs Page: Displays security and operational audit records from SQLite.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
)
from app.storage.repository import storage_repo


class AuditPage(QWidget):
    """Audit Trail and Compliance viewer."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #1A2234; border: 1px solid #26334D; border-radius: 8px; padding: 12px;")
        h_layout = QHBoxLayout(header_card)

        title = QLabel("لاگ‌های ردیابی و امنیت (Audit Trail)")
        title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: bold;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        self.btn_refresh = QPushButton("🔄 به‌روزرسانی لاگ‌ها")
        self.btn_refresh.setProperty("class", "secondary-btn")
        self.btn_refresh.clicked.connect(self.load_audit_logs)
        h_layout.addWidget(self.btn_refresh)
        layout.addWidget(header_card)

        # Table
        self.table_logs = QTableWidget()
        self.table_logs.setColumnCount(8)
        self.table_logs.setHorizontalHeaderLabels([
            "ردیف", "زمان", "کاربر", "عملیات", "ابزار", "دیتابیس", "مدت زمان (ms)", "وضعیت"
        ])
        self.table_logs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_logs)

        self.load_audit_logs()

    def load_audit_logs(self) -> None:
        """Fetch audit records from SQLite."""
        logs = storage_repo.get_recent_audit_logs(limit=100)
        self.table_logs.setRowCount(len(logs))

        for r_idx, log in enumerate(logs):
            self.table_logs.setItem(r_idx, 0, QTableWidgetItem(str(log.get("id", ""))))
            
            # Format timestamp nicely
            ts = log.get("timestamp", "")
            if "T" in ts:
                ts = ts.replace("T", " ")[:19]
            self.table_logs.setItem(r_idx, 1, QTableWidgetItem(ts))
            self.table_logs.setItem(r_idx, 2, QTableWidgetItem(log.get("user", "")))
            self.table_logs.setItem(r_idx, 3, QTableWidgetItem(log.get("action", "")))
            self.table_logs.setItem(r_idx, 4, QTableWidgetItem(log.get("tool", "") or "-"))
            self.table_logs.setItem(r_idx, 5, QTableWidgetItem(log.get("target_database", "") or "-"))
            self.table_logs.setItem(r_idx, 6, QTableWidgetItem(str(log.get("duration_ms", 0.0))))

            success = bool(log.get("success", 1))
            status_item = QTableWidgetItem("موفق" if success else "خطا / ناموفق")
            status_item.setForeground(Qt.green if success else Qt.red)
            self.table_logs.setItem(r_idx, 7, status_item)
