"""
Integration Hub Page for connecting external C# conversion, report builder,
and installer programs to the local Sepehryar AI Copilot REST API.
"""
import json
import threading
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QLineEdit,
    QSpinBox,
    QFrame,
    QApplication,
    QMessageBox,
)
from app.config.settings import settings
from app.agent.cognitive_engine import cognitive_engine

# C# Drop-in Helper Code Template
CSHARP_CODE_SNIPPET = r"""// ============================================================================
// کلاس آماده سی‌شارپ جهت اتصال برنامه تبدیل و گزارش‌ساز به هوش سپهریار
// بدون نیاز به هیچ کتابخانه اضافی (فقط System.Net.Http و System.Text.Json)
// ============================================================================
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

public static class SepehryarBrainClient
{
    private static readonly HttpClient _http = new HttpClient();
    private static string _baseUrl = "http://127.0.0.1:8080";

    public static void SetServerUrl(string url) => _baseUrl = url.TrimEnd('/');

    /// <summary>
    /// پرسش معماری دیتابیس و دریافت تحلیل ۴ مرحله‌ای و اسکریپت تراکنشی
    /// </summary>
    public static async Task<string> AskCopilotAsync(string question)
    {
        var payload = JsonSerializer.Serialize(new { query = question });
        var content = new StringContent(payload, Encoding.UTF8, "application/json");
        
        var resp = await _http.PostAsync($"{_baseUrl}/api/copilot/ask", content);
        resp.EnsureSuccessStatusCode();
        
        var json = await resp.Content.ReadAsStringAsync();
        using var doc = JsonDocument.Parse(json);
        return doc.RootElement.GetProperty("formatted_markdown").GetString();
    }

    /// <summary>
    /// سنتز خودکار اسکریپت تراکنشی برای سناریوهای تعریف شخص، فاکتور، سند افتتاحیه و ...
    /// </summary>
    public static async Task<string> GenerateScriptAsync(string scenario, object parameters)
    {
        var payload = JsonSerializer.Serialize(new { scenario, @params = parameters, language = "sql" });
        var content = new StringContent(payload, Encoding.UTF8, "application/json");

        var resp = await _http.PostAsync($"{_baseUrl}/api/copilot/generate-script", content);
        resp.EnsureSuccessStatusCode();

        var json = await resp.Content.ReadAsStringAsync();
        using var doc = JsonDocument.Parse(json);
        return doc.RootElement.GetProperty("script").GetString();
    }

    /// <summary>
    /// اعتبارسنجی آرایه‌ای از رکوردها قبل از تزریق به دیتابیس سپهریار
    /// </summary>
    public static async Task<string> LintDatasetAsync(string scenario, object dataset)
    {
        var payload = JsonSerializer.Serialize(new { scenario, dataset });
        var content = new StringContent(payload, Encoding.UTF8, "application/json");

        var resp = await _http.PostAsync($"{_baseUrl}/api/copilot/lint-data", content);
        resp.EnsureSuccessStatusCode();

        return await resp.Content.ReadAsStringAsync();
    }
}
"""

PYTHON_CODE_SNIPPET = r"""# قطعه کد پایتون جهت اتصال سریع به سرویس هوش سپهریار
import requests

API_URL = "http://127.0.0.1:8080"

def ask_sepehryar(question: str) -> str:
    res = requests.post(f"{API_URL}/api/copilot/ask", json={"query": question})
    return res.json().get("formatted_markdown", "")

def get_transaction_script(scenario: str, params: dict) -> str:
    res = requests.post(f"{API_URL}/api/copilot/generate-script", json={
        "scenario": scenario,
        "params": params,
        "language": "sql"
    })
    return res.json().get("script", "")

def validate_data(dataset: list) -> dict:
    res = requests.post(f"{API_URL}/api/copilot/lint-data", json={
        "scenario": "migration",
        "dataset": dataset
    })
    return res.json()
"""


class IntegrationHubPage(QWidget):
    """Central control panel for connecting external tools to Sepehryar AI."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self._server_running = False
        self._server_thread = None

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # 1. Header Card (Server Status & Control)
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #172033;
                border: 1px solid #2B384E;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        h_layout = QHBoxLayout(header_card)
        h_layout.setSpacing(16)

        # Title and description
        v_title = QVBoxLayout()
        lbl_h_title = QLabel("🔌 مرکز اتصال به برنامه‌های تبدیل، گزارش‌ساز و اینستالر")
        lbl_h_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        lbl_h_desc = QLabel("سرویس REST API پرسرعت و آفلاین جهت مشاوره معماری، تولید اسکریپت تراکنشی و خطایابی داده‌ها.")
        lbl_h_desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        v_title.addWidget(lbl_h_title)
        v_title.addWidget(lbl_h_desc)
        h_layout.addLayout(v_title, stretch=1)

        # Status badge
        self.lbl_status = QLabel("● آماده اتصال (Port 8080)")
        self.lbl_status.setStyleSheet("""
            QLabel {
                background-color: #064E3B;
                color: #34D399;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 6px;
                border: 1px solid #059669;
            }
        """)
        h_layout.addWidget(self.lbl_status)

        # Copy URL Button
        self.btn_copy_url = QPushButton("📋 کپی آدرس API")
        self.btn_copy_url.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        self.btn_copy_url.clicked.connect(self._copy_api_url)
        h_layout.addWidget(self.btn_copy_url)

        main_layout.addWidget(header_card)

        # 2. Tabs Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #2B384E;
                background-color: #131A29;
                border-radius: 10px;
                padding: 16px;
            }
            QTabBar::tab {
                background-color: #1E293B;
                color: #94A3B8;
                font-weight: bold;
                padding: 10px 20px;
                margin-left: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #2563EB;
                color: #FFFFFF;
            }
        """)

        # Tab 1: C# Integration
        self.tabs.addTab(self._create_csharp_tab(), "💻 کد آماده سی‌شارپ (C# .NET)")

        # Tab 2: Python Integration
        self.tabs.addTab(self._create_python_tab(), "🐍 کد پایتون (Python)")

        # Tab 3: Live Sandbox
        self.tabs.addTab(self._create_sandbox_tab(), "🧪 تست زنده و فوری (Sandbox)")

        # Tab 4: Data Linter
        self.tabs.addTab(self._create_linter_tab(), "🛡️ بازرس داده‌ها (Data Linter)")

        main_layout.addWidget(self.tabs, stretch=1)

    def _create_csharp_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        info = QLabel("این کلاس را مستقیماً داخل پروژه سی‌شارپ برنامه تبدیل یا گزارش‌ساز خود کپی کنید:")
        info.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 13px;")
        layout.addWidget(info)

        editor = QTextEdit()
        editor.setPlainText(CSHARP_CODE_SNIPPET)
        editor.setReadOnly(True)
        editor.setStyleSheet("""
            QTextEdit {
                background-color: #0E131F;
                color: #F8FAFC;
                border: 1px solid #1E293B;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 12px;
            }
        """)
        layout.addWidget(editor, stretch=1)

        btn_copy = QPushButton("📋 کپی کامل کد سی‌شارپ (SepehryarBrainClient.cs)")
        btn_copy.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 10px; border-radius: 8px;")
        btn_copy.clicked.connect(lambda: self._copy_text(CSHARP_CODE_SNIPPET, btn_copy))
        layout.addWidget(btn_copy)

        return w

    def _create_python_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        info = QLabel("نمونه کد پایتون جهت استفاده در اسکریپت‌ها یا میکروسرویس‌ها:")
        info.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 13px;")
        layout.addWidget(info)

        editor = QTextEdit()
        editor.setPlainText(PYTHON_CODE_SNIPPET)
        editor.setReadOnly(True)
        editor.setStyleSheet("""
            QTextEdit {
                background-color: #0E131F;
                color: #F8FAFC;
                border: 1px solid #1E293B;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 12px;
            }
        """)
        layout.addWidget(editor, stretch=1)

        btn_copy = QPushButton("📋 کپی کد پایتون")
        btn_copy.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 10px; border-radius: 8px;")
        btn_copy.clicked.connect(lambda: self._copy_text(PYTHON_CODE_SNIPPET, btn_copy))
        layout.addWidget(btn_copy)

        return w

    def _create_sandbox_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        layout.addWidget(QLabel("پرسش یا سناریوی آزمایشی را وارد کرده و پاسخ زنده موتور را بررسی کنید:"))

        row = QHBoxLayout()
        self.txt_sandbox_query = QLineEdit()
        self.txt_sandbox_query.setText("چطور مشتری جدید ثبت کنم و حسابش رو وصل کنم؟")
        self.txt_sandbox_query.setStyleSheet("background-color: #1E293B; color: white; padding: 8px; border-radius: 6px;")
        row.addWidget(self.txt_sandbox_query, stretch=1)

        btn_test = QPushButton("ارسال و آزمایش ↵")
        btn_test.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
        btn_test.clicked.connect(self._run_sandbox_test)
        row.addWidget(btn_test)
        layout.addLayout(row)

        self.txt_sandbox_output = QTextEdit()
        self.txt_sandbox_output.setReadOnly(True)
        self.txt_sandbox_output.setStyleSheet("background-color: #0E131F; color: #38BDF8; font-family: 'Consolas', monospace; padding: 10px;")
        layout.addWidget(self.txt_sandbox_output, stretch=1)

        return w

    def _create_linter_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        layout.addWidget(QLabel("نمونه داده‌های استخراج‌شده از اکسل یا نرم‌افزار مبدأ (JSON) را وارد نمایید تا قبل از درج در سپهریار خطایابی شوند:"))

        sample_data = json.dumps([
            {"name": "علی محمدی 09131112233", "personcod": 0, "bed": -5000000, "is_bank": True, "type": 1},
            {"name": "شرکت پخش سینا", "personcod": 1500, "bed": 12000000, "bes": 0, "is_bank": False, "type": 2}
        ], indent=2, ensure_ascii=False)

        self.txt_linter_input = QTextEdit()
        self.txt_linter_input.setPlainText(sample_data)
        self.txt_linter_input.setStyleSheet("background-color: #0E131F; color: #F8FAFC; font-family: 'Consolas', monospace; padding: 10px;")
        layout.addWidget(self.txt_linter_input, stretch=1)

        btn_lint = QPushButton("🔍 بازرسی داده‌ها و کشف تله‌های پنهان دیتابیس")
        btn_lint.setStyleSheet("background-color: #D97706; color: white; font-weight: bold; padding: 10px; border-radius: 8px;")
        btn_lint.clicked.connect(self._run_linter_check)
        layout.addWidget(btn_lint)

        self.txt_linter_output = QTextEdit()
        self.txt_linter_output.setReadOnly(True)
        self.txt_linter_output.setStyleSheet("background-color: #0E131F; color: #E2E8F0; font-family: 'Segoe UI', Tahoma; padding: 10px;")
        layout.addWidget(self.txt_linter_output, stretch=1)

        return w

    def _copy_api_url(self) -> None:
        url = f"http://127.0.0.1:{settings.api_port}"
        QApplication.clipboard().setText(url)
        self.btn_copy_url.setText("✓ کپی شد!")
        QTimer.singleShot(2000, lambda: self.btn_copy_url.setText("📋 کپی آدرس API"))

    def _copy_text(self, text: str, btn: QPushButton) -> None:
        QApplication.clipboard().setText(text)
        orig = btn.text()
        btn.setText("✓ در کلیپ‌بورد کپی شد!")
        QTimer.singleShot(2000, lambda: btn.setText(orig))

    def _run_sandbox_test(self) -> None:
        q = self.txt_sandbox_query.text().strip()
        if not q:
            return
        res = cognitive_engine.reason_and_solve(q)
        self.txt_sandbox_output.setPlainText(res.to_formatted_markdown())

    def _run_linter_check(self) -> None:
        raw = self.txt_linter_input.toPlainText().strip()
        try:
            dataset = json.loads(raw)
            if not isinstance(dataset, list):
                dataset = [dataset]
            report = cognitive_engine.lint_dataset("migration", dataset)
            lines = [
                f"🛡️ نتیجه بازرسی داده‌ها: {'✅ امن برای درج' if report['is_safe'] else '⚠️ دارای ریسک و خطای ساختاری'}\n",
                f"• تعداد خطاهای بحرانی (باعث تخریب دیتابیس): {len(report['errors'])}",
                f"• تعداد هشدارها: {len(report['warnings'])}\n"
            ]
            if report['errors']:
                lines.append("❌ خطاهای بحرانی:")
                for e in report['errors']:
                    lines.append(f"  - {e}")
            if report['warnings']:
                lines.append("\n⚠️ هشدارها:")
                for w in report['warnings']:
                    lines.append(f"  - {w}")
            if report['recommendations']:
                lines.append("\n💡 توصیه‌های معماری:")
                for r in report['recommendations']:
                    lines.append(f"  - {r}")

            self.txt_linter_output.setPlainText("\n".join(lines))
        except Exception as e:
            self.txt_linter_output.setPlainText(f"❌ خطا در خواندن فرمت JSON: {e}")
