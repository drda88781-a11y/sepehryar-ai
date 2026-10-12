"""
Always-on-top Floating Spotlight Bar for Sepehryar AI Engine.
Allows developers to query Sepehryar architecture and database rules
from a sleek top-screen overlay while working in Visual Studio, Excel, or other apps.
"""
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QLabel,
    QFrame,
    QApplication,
)
from app.agent.orchestrator import agent_orchestrator


class SpotlightBar(QWidget):
    """Floating, always-on-top query bar designed for the top of the screen."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Window
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(780, 70)
        self._is_expanded = False
        self._drag_pos = QPoint()

        self._init_ui()
        self._center_top()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(6)

        # Main glassmorphic container
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: #0E131F;
                border: 2px solid #2563EB;
                border-radius: 14px;
            }
        """)
        self.card_layout = QVBoxLayout(self.container)
        self.card_layout.setContentsMargins(12, 8, 12, 10)
        self.card_layout.setSpacing(8)

        # Top Bar (Input Row)
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # AI Badge Icon
        badge = QLabel("🧠")
        badge.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        top_row.addWidget(badge)

        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("از هوش سپهریار بپرسید... (مثلاً: ثبت سند افتتاحیه، مهار تریگر، personcod چیست)")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #172033;
                color: #FFFFFF;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                font-family: 'Segoe UI', Tahoma, sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #38BDF8;
                background-color: #1E293B;
            }
        """)
        self.input_field.returnPressed.connect(self._handle_ask)
        top_row.addWidget(self.input_field, stretch=1)

        # Ask Button
        self.btn_ask = QPushButton("پرسش ↵")
        self.btn_ask.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        self.btn_ask.clicked.connect(self._handle_ask)
        top_row.addWidget(self.btn_ask)

        # Close / Minimize Button
        btn_close = QPushButton("✕")
        btn_close.setToolTip("بستن نوار شناور (Esc)")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94A3B8;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #EF4444;
            }
        """)
        btn_close.clicked.connect(self.hide)
        top_row.addWidget(btn_close)

        self.card_layout.addLayout(top_row)

        # Result Browser (hidden initially)
        self.result_box = QTextBrowser()
        self.result_box.setOpenExternalLinks(True)
        self.result_box.setStyleSheet("""
            QTextBrowser {
                background-color: #131A29;
                color: #E2E8F0;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                font-family: 'Segoe UI', Tahoma, sans-serif;
            }
        """)
        self.result_box.setVisible(False)
        self.card_layout.addWidget(self.result_box)

        # Bottom Actions row (Copy & Status)
        self.bottom_row = QHBoxLayout()
        self.lbl_status = QLabel("⚡ آماده پاسخ‌گویی آفلاین")
        self.lbl_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: bold; background: transparent; border: none;")
        self.bottom_row.addWidget(self.lbl_status)
        self.bottom_row.addStretch()

        self.btn_copy = QPushButton("📋 کپی پاسخ")
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #FFFFFF;
            }
        """)
        self.btn_copy.clicked.connect(self._copy_response)
        self.btn_copy.setVisible(False)
        self.bottom_row.addWidget(self.btn_copy)

        self.card_layout.addLayout(self.bottom_row)
        outer_layout.addWidget(self.container)

    def _center_top(self) -> None:
        """Position window at top center of primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + 25
            self.move(x, y)

    def _handle_ask(self) -> None:
        q = self.input_field.text().strip()
        if not q:
            return

        self.lbl_status.setText("🧠 در حال تحلیل معماری سپهریار...")
        QApplication.processEvents()

        try:
            resp = agent_orchestrator.process_query(q)
            self.result_box.setMarkdown(resp.persian_answer)
            self.result_box.setVisible(True)
            self.btn_copy.setVisible(True)
            self.lbl_status.setText(f"⚡ پاسخ در {resp.duration_ms:.1f} میلی‌ثانیه آماده شد.")

            # Expand window height
            self.resize(780, 480)
            self._is_expanded = True
        except Exception as e:
            self.lbl_status.setText(f"❌ خطا: {e}")

    def _copy_response(self) -> None:
        text = self.result_box.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.btn_copy.setText("✓ کپی شد!")
            self.btn_copy.setStyleSheet("background-color: #065F46; color: #34D399; border-radius: 6px; padding: 4px 12px;")

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            if self._is_expanded:
                self.result_box.setVisible(False)
                self.btn_copy.setVisible(False)
                self.resize(780, 70)
                self._is_expanded = False
            else:
                self.hide()
        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
