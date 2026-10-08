"""
Interactive Persian & RTL Chat page for communicating with the Sepehryar AI Agent.
Displays user messages, AI answers, tool badges, execution durations, and SQL result previews.
"""
from typing import Optional
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from app.agent.orchestrator import agent_orchestrator
from app.agent.schemas import AgentResponse


class AgentWorker(QThread):
    """Worker thread running agent orchestration in background."""
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, query: str) -> None:
        super().__init__()
        self.query = query

    def run(self) -> None:
        try:
            res = agent_orchestrator.process_query(self.query)
            self.finished.emit(res)
        except Exception as e:
            self.failed.emit(str(e))


class ChatPage(QWidget):
    """Chat interface with the Sepehryar AI Engine."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.worker: Optional[AgentWorker] = None
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header card
        header = QFrame()
        header.setStyleSheet("background-color: #1A2234; border: 1px solid #26334D; border-radius: 8px; padding: 10px;")
        h_layout = QHBoxLayout(header)
        h_title = QLabel("گفت‌وگو با مغز هوشمند سپهریار (AI Chat Assistant)")
        h_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: bold;")
        h_sub = QLabel("● آماده پاسخ‌گویی ۱۰۰٪ محلی و آفلاین")
        h_sub.setStyleSheet("color: #00A86B; font-size: 12px; font-weight: bold;")
        h_layout.addWidget(h_title)
        h_layout.addStretch()
        h_layout.addWidget(h_sub)
        layout.addWidget(header)

        # Quick Suggestion Chips
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(8)
        chips = [
            "تعداد کالاها چقدره؟",
            "۵ مشتری با بیشترین بدهی",
            "ارتباط TblKala با TR چیه؟",
            "چرا SQL وصل نمیشه؟",
            "بررسی سلامت سرور",
        ]
        for chip_text in chips:
            btn = QPushButton(chip_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #242E44;
                    color: #94A3B8;
                    border: 1px solid #334155;
                    border-radius: 12px;
                    padding: 4px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #0F52BA;
                    color: #FFFFFF;
                }
            """)
            btn.clicked.connect(lambda checked=False, t=chip_text: self.send_prompt(t))
            chips_layout.addWidget(btn)
        chips_layout.addStretch()
        layout.addLayout(chips_layout)

        # Chat Message Stream Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #26334D; border-radius: 8px; background-color: #121824; }")

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background-color: #121824;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(16, 16, 16, 16)
        self.chat_layout.setSpacing(14)
        self.chat_layout.addStretch()

        scroll.setWidget(self.chat_container)
        layout.addWidget(scroll)

        # Input Bar
        input_bar = QHBoxLayout()
        input_bar.setSpacing(10)

        self.input_query = QLineEdit()
        self.input_query.setPlaceholderText("پرسش خود را به زبان فارسی مطرح فرمایید (مثلاً: موجودی انبار یا تعداد کالاها)...")
        self.input_query.setStyleSheet("""
            QLineEdit {
                background-color: #1A2234;
                color: #FFFFFF;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
            }
        """)
        self.input_query.returnPressed.connect(self.on_submit_query)

        self.btn_send = QPushButton("ارسال پیام ↵")
        self.btn_send.setProperty("class", "primary-btn")
        self.btn_send.setStyleSheet("padding: 10px 20px; font-weight: bold;")
        self.btn_send.clicked.connect(self.on_submit_query)

        input_bar.addWidget(self.input_query)
        input_bar.addWidget(self.btn_send)
        layout.addLayout(input_bar)

        # Add initial welcome message from AI
        self.add_ai_bubble(
            "سلام! من دستیار هوشمند محلی نرم‌افزار حسابداری سپهریار هستم. "
            "می‌توانید درباره کالاها، مشتریان، فاکتورها، روابط جداول یا عیب‌یابی سرور از من سؤال بپرسید."
        )

    def on_submit_query(self) -> None:
        text = self.input_query.text().strip()
        if not text:
            return
        self.input_query.clear()
        self.send_prompt(text)

    def send_prompt(self, text: str) -> None:
        self.add_user_bubble(text)
        self.btn_send.setEnabled(False)

        self.worker = AgentWorker(text)
        self.worker.finished.connect(self.on_agent_finished)
        self.worker.failed.connect(self.on_agent_failed)
        self.worker.start()

    def on_agent_finished(self, response: AgentResponse) -> None:
        self.btn_send.setEnabled(True)
        self.add_ai_response_card(response)

    def on_agent_failed(self, error_str: str) -> None:
        self.btn_send.setEnabled(True)
        self.add_ai_bubble(f"❌ خطا در اجرای درخواست: {error_str}")

    def add_user_bubble(self, text: str) -> None:
        row = QHBoxLayout()
        row.addStretch()

        bubble = QFrame()
        bubble.setStyleSheet("""
            QFrame {
                background-color: #0F52BA;
                border-radius: 12px;
                padding: 10px 14px;
                max-width: 600px;
            }
        """)
        b_layout = QVBoxLayout(bubble)
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #FFFFFF; font-size: 13px;")
        lbl.setWordWrap(True)
        b_layout.addWidget(lbl)

        row.addWidget(bubble)
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, row)

    def add_ai_bubble(self, text: str) -> None:
        row = QHBoxLayout()
        bubble = QFrame()
        bubble.setStyleSheet("""
            QFrame {
                background-color: #1A2234;
                border: 1px solid #26334D;
                border-radius: 12px;
                padding: 12px 16px;
                max-width: 750px;
            }
        """)
        b_layout = QVBoxLayout(bubble)
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #F8FAFC; font-size: 13px; line-height: 1.5;")
        lbl.setWordWrap(True)
        b_layout.addWidget(lbl)

        row.addWidget(bubble)
        row.addStretch()
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, row)

    def add_ai_response_card(self, res: AgentResponse) -> None:
        row = QHBoxLayout()
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1A2234;
                border: 1px solid #26334D;
                border-radius: 12px;
                padding: 14px 18px;
                max-width: 800px;
            }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(10)

        # 1. Main Persian Answer
        lbl_ans = QLabel(res.persian_answer)
        lbl_ans.setStyleSheet("color: #F8FAFC; font-size: 13px; font-weight: 500;")
        lbl_ans.setWordWrap(True)
        c_layout.addWidget(lbl_ans)

        # 2. SQL Plan Preview if generated
        if res.sql_plan:
            sql_box = QFrame()
            sql_box.setStyleSheet("background-color: #121824; border: 1px solid #334155; border-radius: 6px; padding: 8px;")
            s_layout = QVBoxLayout(sql_box)
            lbl_sql_title = QLabel(f"⚡ دستور SQL اجرا شده ({res.sql_plan.goal}):")
            lbl_sql_title.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: bold;")
            lbl_sql = QLabel(res.sql_plan.generated_sql)
            lbl_sql.setStyleSheet("color: #00A86B; font-family: monospace; font-size: 12px;")
            lbl_sql.setWordWrap(True)
            s_layout.addWidget(lbl_sql_title)
            s_layout.addWidget(lbl_sql)
            c_layout.addWidget(sql_box)

        # 3. Data preview table if results returned
        if res.sql_result and res.sql_result.get("rows"):
            rows = res.sql_result["rows"][:5]  # preview top 5 rows
            cols = res.sql_result.get("columns", [])
            if cols and rows:
                t_preview = QTableWidget()
                t_preview.setMaximumHeight(140)
                t_preview.setColumnCount(len(cols))
                t_preview.setRowCount(len(rows))
                t_preview.setHorizontalHeaderLabels(cols)
                t_preview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                for r_i, r_data in enumerate(rows):
                    for c_i, c_name in enumerate(cols):
                        val = r_data.get(c_name, "")
                        t_preview.setItem(r_i, c_i, QTableWidgetItem(str(val)))
                c_layout.addWidget(t_preview)

        # 4. Meta Badges Row
        badge_row = QHBoxLayout()
        badge_row.setSpacing(8)

        intent_lbl = QLabel(f"🏷️ قصد: {res.intent.value}")
        intent_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; background-color: #242E44; border-radius: 4px; padding: 2px 6px;")
        badge_row.addWidget(intent_lbl)

        dur_lbl = QLabel(f"⏱️ {res.duration_ms:.1f} ms")
        dur_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; background-color: #242E44; border-radius: 4px; padding: 2px 6px;")
        badge_row.addWidget(dur_lbl)

        for t in res.tools_used:
            t_lbl = QLabel(f"🔧 {t.tool_name}")
            t_lbl.setStyleSheet("color: #38BDF8; font-size: 11px; background-color: #1E293B; border-radius: 4px; padding: 2px 6px;")
            badge_row.addWidget(t_lbl)

        badge_row.addStretch()
        c_layout.addLayout(badge_row)

        row.addWidget(card)
        row.addStretch()
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, row)
