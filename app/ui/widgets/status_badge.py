"""
Status badge indicator widget displaying glowing state dots and Persian labels.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


class StatusBadge(QWidget):
    """Visual status pill badge with a colored indicator dot and label."""

    COLORS = {
        "online": "#00A86B",     # Jade Green
        "offline": "#E63946",    # Coral Red
        "warning": "#FFBF00",    # Amber
        "neutral": "#94A3B8",    # Slate Muted
        "blue": "#38BDF8",       # Sky Blue
    }

    def __init__(self, title: str, status_text: str, state: str = "online", parent: QWidget = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 500;")

        self.dot_lbl = QLabel("●")
        self.dot_lbl.setStyleSheet(f"color: {self.COLORS.get(state, '#00A86B')}; font-size: 14px;")

        self.status_lbl = QLabel(status_text)
        self.status_lbl.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: bold;")

        layout.addWidget(self.title_lbl)
        layout.addStretch()
        layout.addWidget(self.dot_lbl)
        layout.addWidget(self.status_lbl)

        self.setStyleSheet("""
            QWidget {
                background-color: #1A2234;
                border: 1px solid #26334D;
                border-radius: 6px;
            }
        """)

    def update_status(self, status_text: str, state: str) -> None:
        self.status_lbl.setText(status_text)
        color = self.COLORS.get(state, "#94A3B8")
        self.dot_lbl.setStyleSheet(f"color: {color}; font-size: 14px;")
