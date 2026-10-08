"""
Query Explorer Page: Safe Read-Only SQL execution and tabular results explorer.
"""
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QMessageBox,
)
from app.config.settings import settings
from app.database.safe_sql import safe_sql_executor, SafeSQLValidator


class QueryPage(QWidget):
    """Query Explorer for executing safe read-only SQL queries."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header & Toolbar Card
        top_card = QFrame()
        top_card.setStyleSheet("background-color: #1A2234; border: 1px solid #26334D; border-radius: 8px; padding: 12px;")
        t_layout = QVBoxLayout(top_card)
        t_layout.setSpacing(10)

        title = QLabel("کاوشگر کوئری‌های امن (Safe SQL Query Explorer)")
        title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: bold;")
        t_layout.addWidget(title)

        # Editor
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("دستور SELECT را در این قسمت وارد فرمایید...\nمثال: SELECT TOP 10 IDKala, NameKala, GhimatForosh, Mogodi FROM TblKala")
        self.editor.setPlainText("SELECT TOP 20 IDKala, NameKala, Barcode, GhimatForosh, Mogodi FROM TblKala")
        self.editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #121824;
                color: #38BDF8;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        self.editor.setMaximumHeight(110)
        t_layout.addWidget(self.editor)

        # Buttons row
        b_row = QHBoxLayout()
        self.btn_run = QPushButton("▶ اجرای ایمن کوئری (SELECT)")
        self.btn_run.setProperty("class", "primary-btn")
        self.btn_run.clicked.connect(self.on_execute_query)

        self.btn_clear = QPushButton("پاکسازی")
        self.btn_clear.setProperty("class", "secondary-btn")
        self.btn_clear.clicked.connect(lambda: self.editor.clear())

        self.lbl_query_status = QLabel("دستورات مخرب (INSERT, UPDATE, DELETE, DROP) به صورت خودکار مسدود می‌شوند.")
        self.lbl_query_status.setStyleSheet("color: #94A3B8; font-size: 12px;")

        b_row.addWidget(self.btn_run)
        b_row.addWidget(self.btn_clear)
        b_row.addStretch()
        b_row.addWidget(self.lbl_query_status)
        t_layout.addLayout(b_row)

        layout.addWidget(top_card)

        # Results Table
        self.table_results = QTableWidget()
        self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_results)

    def on_execute_query(self) -> None:
        """Validate and execute query."""
        sql = self.editor.toPlainText().strip()
        if not sql:
            return

        # Pre-validate
        is_safe, reason = SafeSQLValidator.validate_query(sql)
        if not is_safe:
            self.lbl_query_status.setStyleSheet("color: #E63946; font-weight: bold;")
            self.lbl_query_status.setText(f"❌ کوئری مسدود شد: {reason}")
            QMessageBox.critical(self, "خطای امنیتی کوئری", f"دستور ارسالی امن نیست:\n\n{reason}")
            return

        try:
            res = safe_sql_executor.execute_readonly_query(
                sql=sql,
                database=settings.sql_database,
                max_rows=100,
                mask_sensitive=True
            )

            cols = res["columns"]
            rows = res["rows"]
            duration = res["duration_ms"]
            is_mock = res.get("is_mock", False)

            self.table_results.clear()
            self.table_results.setColumnCount(len(cols))
            self.table_results.setRowCount(len(rows))
            self.table_results.setHorizontalHeaderLabels(cols)

            for r_idx, row in enumerate(rows):
                for c_idx, col in enumerate(cols):
                    val = row.get(col, "")
                    self.table_results.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

            mock_tag = " (حالت دمو آفلاین)" if is_mock else ""
            self.lbl_query_status.setStyleSheet("color: #00A86B; font-weight: bold;")
            self.lbl_query_status.setText(f"✅ کوئری در {duration:.1f} میلی‌ثانیه اجرا شد ({len(rows)} ردیف بازگردانده شد){mock_tag}")

        except Exception as e:
            self.lbl_query_status.setStyleSheet("color: #E63946; font-weight: bold;")
            self.lbl_query_status.setText(f"❌ خطا در اجرای کوئری: {e}")
            QMessageBox.critical(self, "خطای پایگاه داده", str(e))
