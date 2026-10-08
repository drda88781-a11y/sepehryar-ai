"""
Database Analysis page: SQL Server connection manager, deep schema scanner,
table/column introspection, relationships viewer, and sample data explorer.
"""
from typing import Optional, Any
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QHeaderView,
    QFrame,
    QSplitter,
    QMessageBox,
    QRadioButton,
    QButtonGroup,
)
from app.config.settings import settings
from app.database.connection import db_connection_manager
from app.database.metadata import DatabaseSchema
from app.database.mock_provider import get_mock_database_schema, get_mock_sample_rows
from app.database.safe_sql import safe_sql_executor
from app.database.scanner import database_scanner
from app.storage.repository import storage_repo


class ScanWorker(QThread):
    """Background worker for deep database scanning without freezing UI."""
    scan_finished = Signal(object)
    scan_failed = Signal(str)

    def __init__(self, server: str, database: str, auth_type: str, username: str, password: str) -> None:
        super().__init__()
        self.server = server
        self.database = database
        self.auth_type = auth_type
        self.username = username
        self.password = password

    def run(self) -> None:
        try:
            schema = database_scanner.scan_database(
                server=self.server,
                database=self.database,
                auth_type=self.auth_type,
                username=self.username,
                password=self.password,
                save_to_storage=True
            )
            self.scan_finished.emit(schema)
        except Exception as e:
            self.scan_failed.emit(str(e))


class DatabasePage(QWidget):
    """Main Database Analysis page."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.current_schema: Optional[DatabaseSchema] = None
        self.scan_worker: Optional[ScanWorker] = None
        self.init_ui()
        self.load_cached_schema()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # 1. Connection & Scan Bar Card
        conn_card = QFrame()
        conn_card.setStyleSheet("background-color: #1A2234; border: 1px solid #26334D; border-radius: 8px; padding: 12px;")
        conn_layout = QVBoxLayout(conn_card)
        conn_layout.setSpacing(10)

        # Row 1: Inputs
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        lbl_srv = QLabel("سرور SQL:")
        lbl_srv.setStyleSheet("color: #94A3B8; font-weight: bold;")
        self.input_server = QLineEdit(settings.sql_server)
        self.input_server.setPlaceholderText(".\\SEPEHRYAR2019 یا IP سرور")
        self.input_server.setMinimumWidth(160)

        lbl_db = QLabel("نام دیتابیس:")
        lbl_db.setStyleSheet("color: #94A3B8; font-weight: bold;")
        self.combo_db = QComboBox()
        self.combo_db.setEditable(True)
        self.combo_db.addItem(settings.sql_database)
        self.combo_db.setMinimumWidth(180)

        # Auth radio
        self.radio_win = QRadioButton("Windows Auth")
        self.radio_sql = QRadioButton("SQL Auth")
        self.radio_win.setChecked(True)
        auth_group = QButtonGroup(self)
        auth_group.addButton(self.radio_win)
        auth_group.addButton(self.radio_sql)

        self.btn_test = QPushButton("🔗 تست اتصال")
        self.btn_test.setProperty("class", "secondary-btn")
        self.btn_test.clicked.connect(self.on_test_connection)

        self.btn_scan = QPushButton("🚀 اسکن کامل ساختار")
        self.btn_scan.setProperty("class", "primary-btn")
        self.btn_scan.clicked.connect(self.on_start_scan)

        self.btn_demo = QPushButton("📦 بارگذاری دمو آفلاین")
        self.btn_demo.setProperty("class", "success-btn")
        self.btn_demo.clicked.connect(self.on_load_demo)

        row1.addWidget(lbl_srv)
        row1.addWidget(self.input_server)
        row1.addWidget(lbl_db)
        row1.addWidget(self.combo_db)
        row1.addWidget(self.radio_win)
        row1.addWidget(self.radio_sql)
        row1.addWidget(self.btn_test)
        row1.addWidget(self.btn_scan)
        row1.addWidget(self.btn_demo)
        conn_layout.addLayout(row1)

        # Status text label
        self.lbl_status = QLabel("برای تحلیل ساختار، دیتابیس را انتخاب کرده و روی «اسکن کامل ساختار» کلیک فرمایید.")
        self.lbl_status.setStyleSheet("color: #38BDF8; font-size: 12px;")
        conn_layout.addWidget(self.lbl_status)
        layout.addWidget(conn_card)

        # 2. Main Content Splitter (Left: Tables list, Right: Table details tabs)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)

        # Left Pane: Tables List
        left_pane = QFrame()
        left_pane.setStyleSheet("background-color: #1A2234; border: 1px solid #26334D; border-radius: 8px; padding: 10px;")
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        left_header = QLabel("لیست جداول سیستم")
        left_header.setStyleSheet("color: #F8FAFC; font-size: 13px; font-weight: bold;")
        left_layout.addWidget(left_header)

        self.input_filter = QLineEdit()
        self.input_filter.setPlaceholderText("جستجو در جداول (مثلاً Kala)...")
        self.input_filter.textChanged.connect(self.on_filter_tables)
        left_layout.addWidget(self.input_filter)

        self.list_tables = QListWidget()
        self.list_tables.setStyleSheet("""
            QListWidget {
                background-color: #121824;
                border: 1px solid #26334D;
                border-radius: 6px;
                color: #E2E8F0;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #1E293B;
            }
            QListWidget::item:selected {
                background-color: #0F52BA;
                color: #FFFFFF;
                font-weight: bold;
            }
        """)
        self.list_tables.itemSelectionChanged.connect(self.on_table_selected)
        left_layout.addWidget(self.list_tables)

        left_pane.setMinimumWidth(260)
        left_pane.setMaximumWidth(340)
        splitter.addWidget(left_pane)

        # Right Pane: Detailed Tabs
        right_pane = QFrame()
        right_pane.setStyleSheet("background-color: #1A2234; border: 1px solid #26334D; border-radius: 8px; padding: 10px;")
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)

        # Table title header
        self.lbl_selected_table = QLabel("هیچ جدولی انتخاب نشده است.")
        self.lbl_selected_table.setStyleSheet("color: #38BDF8; font-size: 15px; font-weight: bold;")
        self.lbl_table_desc = QLabel("")
        self.lbl_table_desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        right_layout.addWidget(self.lbl_selected_table)
        right_layout.addWidget(self.lbl_table_desc)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: Columns
        self.table_cols = QTableWidget()
        self.table_cols.setColumnCount(6)
        self.table_cols.setHorizontalHeaderLabels(["نام ستون", "نوع داده", "طول", "Nullable", "Identity", "شرح تخصصی سپهریار"])
        self.table_cols.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabs.addTab(self.table_cols, "📌 ستون‌ها (Columns)")

        # Tab 2: Keys & Relationships
        self.table_keys = QTableWidget()
        self.table_keys.setColumnCount(5)
        self.table_keys.setHorizontalHeaderLabels(["نام رابطه / کلید", "نوع", "ستون مبدأ", "جدول و ستون مقصد", "وضعیت"])
        self.table_keys.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabs.addTab(self.table_keys, "🔗 کلیدها و روابط (PK / FK)")

        # Tab 3: Indexes & Triggers
        self.table_idx_trg = QTableWidget()
        self.table_idx_trg.setColumnCount(4)
        self.table_idx_trg.setHorizontalHeaderLabels(["نام آبجکت", "نوع (ایندکس/تریگر)", "ستون‌ها / رویداد", "وضعیت"])
        self.table_idx_trg.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabs.addTab(self.table_idx_trg, "⚡ ایندکس‌ها و تریگرها")

        # Tab 4: Stored Procedures & Views
        self.table_procs = QTableWidget()
        self.table_procs.setColumnCount(3)
        self.table_procs.setHorizontalHeaderLabels(["نام پروسیجر / ویو", "اسکیما", "نوع"])
        self.table_procs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabs.addTab(self.table_procs, "⚙️ پروسیجرها و ویوها")

        # Tab 5: Sample Rows
        sample_widget = QWidget()
        s_layout = QVBoxLayout(sample_widget)
        s_layout.setContentsMargins(4, 4, 4, 4)
        s_layout.setSpacing(8)

        s_bar = QHBoxLayout()
        self.btn_fetch_sample = QPushButton("🔄 دریافت نمونه داده (TOP 20 - ماسک‌شده)")
        self.btn_fetch_sample.setProperty("class", "secondary-btn")
        self.btn_fetch_sample.clicked.connect(self.on_fetch_sample_data)
        s_bar.addWidget(self.btn_fetch_sample)
        s_bar.addStretch()
        s_layout.addLayout(s_bar)

        self.table_sample = QTableWidget()
        s_layout.addWidget(self.table_sample)
        self.tabs.addTab(sample_widget, "👁️ داده‌های نمونه (Sample Data)")

        right_layout.addWidget(self.tabs)
        splitter.addWidget(right_pane)

        layout.addWidget(splitter)

    def load_cached_schema(self) -> None:
        """Load the last scanned database schema from SQLite repository."""
        scanned = storage_repo.list_scanned_databases()
        if scanned:
            latest_name = scanned[0]["database_name"]
            meta_dict = storage_repo.get_database_metadata(latest_name)
            if meta_dict:
                try:
                    self.current_schema = DatabaseSchema(**meta_dict)
                    self.populate_schema_ui(self.current_schema)
                    self.lbl_status.setText(f"اطلاعات دیتابیس '{latest_name}' از حافظه محلی بازیابی شد.")
                except Exception as e:
                    self.lbl_status.setText(f"دیتابیس ذخیره‌شده '{latest_name}' نیاز به اسکن مجدد دارد.")

    def on_test_connection(self) -> None:
        """Test connection to SQL Server."""
        srv = self.input_server.text().strip()
        db = self.combo_db.currentText().strip()
        auth = "windows" if self.radio_win.isChecked() else "sql"

        self.lbl_status.setText("در حال تست اتصال به SQL Server...")
        ok, msg, db_list = db_connection_manager.test_connection(
            server=srv,
            database=db,
            auth_type=auth
        )
        if ok:
            self.lbl_status.setStyleSheet("color: #00A86B; font-weight: bold;")
            self.lbl_status.setText(f"✅ {msg}")
            if db_list:
                cur_text = self.combo_db.currentText()
                self.combo_db.clear()
                self.combo_db.addItems(db_list)
                if cur_text in db_list:
                    self.combo_db.setCurrentText(cur_text)
        else:
            self.lbl_status.setStyleSheet("color: #E63946; font-weight: bold;")
            self.lbl_status.setText(f"❌ {msg}")
            QMessageBox.warning(self, "خطای اتصال به SQL Server", msg)

    def on_start_scan(self) -> None:
        """Launch deep database scanner."""
        srv = self.input_server.text().strip()
        db = self.combo_db.currentText().strip()
        auth = "windows" if self.radio_win.isChecked() else "sql"

        if not db:
            QMessageBox.warning(self, "خطا", "لطفاً نام دیتابیس را وارد نمایید.")
            return

        self.btn_scan.setEnabled(False)
        self.lbl_status.setStyleSheet("color: #38BDF8;")
        self.lbl_status.setText(f"در حال اسکن عمیق دیتابیس '{db}'... لطفاً شکیبا باشید.")

        self.scan_worker = ScanWorker(
            server=srv,
            database=db,
            auth_type=auth,
            username="",
            password=""
        )
        self.scan_worker.scan_finished.connect(self.on_scan_success)
        self.scan_worker.scan_failed.connect(self.on_scan_error)
        self.scan_worker.start()

    def on_scan_success(self, schema: DatabaseSchema) -> None:
        self.btn_scan.setEnabled(True)
        self.current_schema = schema
        self.populate_schema_ui(schema)
        self.lbl_status.setStyleSheet("color: #00A86B; font-weight: bold;")
        self.lbl_status.setText(
            f"✅ اسکن دیتابیس '{schema.database_name}' با موفقیت انجام شد: "
            f"{schema.total_tables} جدول، {schema.total_views} ویو، {schema.total_procs} پروسیجر ذخیره شد."
        )

    def on_scan_error(self, err_msg: str) -> None:
        self.btn_scan.setEnabled(True)
        self.lbl_status.setStyleSheet("color: #E63946; font-weight: bold;")
        self.lbl_status.setText(f"❌ اسکن دیتابیس با شکست مواجه شد: {err_msg}")
        QMessageBox.critical(self, "خطا در اسکن", err_msg)

    def on_load_demo(self) -> None:
        """Load offline mock Sepehryar schema."""
        schema = get_mock_database_schema()
        self.current_schema = schema
        storage_repo.save_database_metadata(
            database_name=schema.database_name,
            server_name=schema.server_name,
            metadata_dict=schema.model_dump()
        )
        self.populate_schema_ui(schema)
        self.lbl_status.setStyleSheet("color: #00A86B; font-weight: bold;")
        self.lbl_status.setText(f"✅ پایگاه داده دمو سپهریار ({schema.total_tables} جدول کلیدی) بارگذاری شد.")

    def populate_schema_ui(self, schema: DatabaseSchema) -> None:
        """Render scanned schema into UI controls."""
        self.list_tables.clear()
        for tbl_name, tbl_meta in sorted(schema.tables.items()):
            desc_text = f" ({tbl_meta.description})" if tbl_meta.description else ""
            item_text = f"{tbl_name} [{tbl_meta.row_count:,} ردیف]{desc_text}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, tbl_name)
            self.list_tables.addItem(item)

        # Populate Procs and Views tab
        self.table_procs.setRowCount(0)
        for p in schema.stored_procedures:
            r = self.table_procs.rowCount()
            self.table_procs.insertRow(r)
            self.table_procs.setItem(r, 0, QTableWidgetItem(p.name))
            self.table_procs.setItem(r, 1, QTableWidgetItem(p.schema_name))
            self.table_procs.setItem(r, 2, QTableWidgetItem("Stored Procedure"))

        for v in schema.views:
            r = self.table_procs.rowCount()
            self.table_procs.insertRow(r)
            self.table_procs.setItem(r, 0, QTableWidgetItem(v.name))
            self.table_procs.setItem(r, 1, QTableWidgetItem(v.schema_name))
            self.table_procs.setItem(r, 2, QTableWidgetItem("View"))

        # Select first table by default
        if self.list_tables.count() > 0:
            self.list_tables.setCurrentRow(0)

    def on_filter_tables(self, query: str) -> None:
        """Filter table names in list widget."""
        q = query.strip().lower()
        for i in range(self.list_tables.count()):
            item = self.list_tables.item(i)
            tbl_name = item.data(Qt.UserRole).lower()
            item.setHidden(q not in tbl_name and q not in item.text().lower())

    def on_table_selected(self) -> None:
        """Display details for currently selected table."""
        items = self.list_tables.selectedItems()
        if not items or not self.current_schema:
            return

        tbl_name = items[0].data(Qt.UserRole)
        tbl_meta = self.current_schema.tables.get(tbl_name)
        if not tbl_meta:
            return

        self.lbl_selected_table.setText(f"جدول: {tbl_name} (اسکیما: {tbl_meta.schema_name} | {tbl_meta.row_count:,} ردیف)")
        desc = tbl_meta.description or "شرح اختصاصی در دیکشنری سپهریار ثبت نشده است."
        self.lbl_table_desc.setText(f"شرح معنایی: {desc}")

        # 1. Fill Columns Tab
        self.table_cols.setRowCount(0)
        for col_name, col in tbl_meta.columns.items():
            r = self.table_cols.rowCount()
            self.table_cols.insertRow(r)
            self.table_cols.setItem(r, 0, QTableWidgetItem(col.name))
            self.table_cols.setItem(r, 1, QTableWidgetItem(col.data_type))
            self.table_cols.setItem(r, 2, QTableWidgetItem(str(col.max_length) if col.max_length else "-"))
            self.table_cols.setItem(r, 3, QTableWidgetItem("بله" if col.is_nullable else "خیر"))
            self.table_cols.setItem(r, 4, QTableWidgetItem("بله" if col.is_identity else "خیر"))
            self.table_cols.setItem(r, 5, QTableWidgetItem(col.description or "-"))

        # 2. Fill Keys & Relationships Tab
        self.table_keys.setRowCount(0)
        for pk in tbl_meta.primary_keys:
            r = self.table_keys.rowCount()
            self.table_keys.insertRow(r)
            self.table_keys.setItem(r, 0, QTableWidgetItem(f"PK_{tbl_name}"))
            self.table_keys.setItem(r, 1, QTableWidgetItem("Primary Key"))
            self.table_keys.setItem(r, 2, QTableWidgetItem(pk))
            self.table_keys.setItem(r, 3, QTableWidgetItem("-"))
            self.table_keys.setItem(r, 4, QTableWidgetItem("کلید اصلی جدول"))

        for rel in self.current_schema.relationships:
            if rel.source_table == tbl_name or rel.target_table == tbl_name:
                r = self.table_keys.rowCount()
                self.table_keys.insertRow(r)
                self.table_keys.setItem(r, 0, QTableWidgetItem(rel.fk_name))
                self.table_keys.setItem(r, 1, QTableWidgetItem("Foreign Key (تخمینی)" if rel.is_inferred else "Foreign Key (رسمی)"))
                self.table_keys.setItem(r, 2, QTableWidgetItem(f"{rel.source_table}.{', '.join(rel.source_columns)}"))
                self.table_keys.setItem(r, 3, QTableWidgetItem(f"{rel.target_table}.{', '.join(rel.target_columns)}"))
                self.table_keys.setItem(r, 4, QTableWidgetItem(rel.description or "-"))

        # 3. Fill Indexes & Triggers Tab
        self.table_idx_trg.setRowCount(0)
        for idx in tbl_meta.indexes:
            r = self.table_idx_trg.rowCount()
            self.table_idx_trg.insertRow(r)
            self.table_idx_trg.setItem(r, 0, QTableWidgetItem(idx.name))
            self.table_idx_trg.setItem(r, 1, QTableWidgetItem("Unique Index" if idx.is_unique else "Index"))
            self.table_idx_trg.setItem(r, 2, QTableWidgetItem(", ".join(idx.columns)))
            self.table_idx_trg.setItem(r, 3, QTableWidgetItem("فعال"))

        for trg in tbl_meta.triggers:
            r = self.table_idx_trg.rowCount()
            self.table_idx_trg.insertRow(r)
            self.table_idx_trg.setItem(r, 0, QTableWidgetItem(trg.name))
            self.table_idx_trg.setItem(r, 1, QTableWidgetItem("Trigger"))
            self.table_idx_trg.setItem(r, 2, QTableWidgetItem(", ".join(trg.events) if trg.events else "DML"))
            self.table_idx_trg.setItem(r, 3, QTableWidgetItem("غیرفعال" if trg.is_disabled else "فعال"))

        # Clear sample data table until explicitly requested
        self.table_sample.setRowCount(0)
        self.table_sample.setColumnCount(0)

    def on_fetch_sample_data(self) -> None:
        """Fetch controlled TOP 20 sample rows for selected table."""
        items = self.list_tables.selectedItems()
        if not items:
            return
        tbl_name = items[0].data(Qt.UserRole)
        db_name = self.combo_db.currentText().strip()

        try:
            query = f"SELECT TOP (20) * FROM {tbl_name}"
            res = safe_sql_executor.execute_readonly_query(
                sql=query,
                database=db_name,
                server=self.input_server.text().strip(),
                max_rows=20,
                mask_sensitive=True
            )
            cols = res["columns"]
            rows = res["rows"]

            self.table_sample.clear()
            self.table_sample.setColumnCount(len(cols))
            self.table_sample.setRowCount(len(rows))
            self.table_sample.setHorizontalHeaderLabels(cols)

            for r_idx, row in enumerate(rows):
                for c_idx, col in enumerate(cols):
                    val = row.get(col, "")
                    self.table_sample.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

        except Exception as e:
            QMessageBox.critical(self, "خطا در دریافت داده‌های نمونه", str(e))
