"""
Summary metric card widget for displaying high-level counts and statistics.
"""
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class MetricCard(QFrame):
    """Card widget displaying a stat title, large number, and subtitle."""

    def __init__(self, title: str, value: str, subtitle: str = "", accent_color: str = "#38BDF8", parent=None) -> None:
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setStyleSheet(f"""
            QFrame.card {{
                background-color: #1A2234;
                border: 1px solid #26334D;
                border-top: 3px solid {accent_color};
                border-radius: 8px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: bold;")

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet("color: #F8FAFC; font-size: 24px; font-weight: bold;")

        self.subtitle_lbl = QLabel(subtitle)
        self.subtitle_lbl.setStyleSheet("color: #64748B; font-size: 11px;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)
        if subtitle:
            layout.addWidget(self.subtitle_lbl)

    def set_value(self, val: str) -> None:
        self.value_lbl.setText(str(val))

    def set_subtitle(self, sub: str) -> None:
        self.subtitle_lbl.setText(str(sub))
