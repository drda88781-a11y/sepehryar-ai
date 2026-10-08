"""
Enterprise Dark Theme styling and stylesheet definitions for PySide6 (Persian & RTL).
"""

APP_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #121824;
    color: #E2E8F0;
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    font-size: 13px;
}

/* Sidebar & Navigation */
#SidebarFrame {
    background-color: #0E131D;
    border-left: 1px solid #1E293B;
    min-width: 220px;
    max-width: 240px;
}

#SidebarTitle {
    color: #FFFFFF;
    font-size: 16px;
    font-weight: bold;
    padding: 18px 12px;
}

#SidebarSubtitle {
    color: #00A86B;
    font-size: 11px;
    font-weight: bold;
    padding-bottom: 12px;
}

QPushButton.nav-btn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: right;
    font-size: 13px;
    font-weight: 500;
}

QPushButton.nav-btn:hover {
    background-color: #1A2234;
    color: #FFFFFF;
}

QPushButton.nav-btn:checked, QPushButton.nav-btn.active {
    background-color: #0F52BA;
    color: #FFFFFF;
    font-weight: bold;
}

/* Cards & Containers */
QFrame.card {
    background-color: #1A2234;
    border: 1px solid #2A364F;
    border-radius: 10px;
    padding: 14px;
}

QGroupBox {
    background-color: #1A2234;
    border: 1px solid #2A364F;
    border-radius: 8px;
    margin-top: 18px;
    font-weight: bold;
    color: #E2E8F0;
    padding-top: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 0 10px;
    color: #38BDF8;
}

/* Buttons */
QPushButton.primary-btn {
    background-color: #0F52BA;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton.primary-btn:hover {
    background-color: #1D63D4;
}

QPushButton.primary-btn:pressed {
    background-color: #0B3E8C;
}

QPushButton.secondary-btn {
    background-color: #242E44;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 14px;
}

QPushButton.secondary-btn:hover {
    background-color: #2F3D59;
}

QPushButton.success-btn {
    background-color: #00A86B;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton.success-btn:hover {
    background-color: #05C47F;
}

/* Inputs & Combos */
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {
    background-color: #121824;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #0F52BA;
}

QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #38BDF8;
}

QComboBox::drop-down {
    border: none;
    padding-left: 6px;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #121824;
    border: 1px solid #26334D;
    border-radius: 8px;
    gridline-color: #1E293B;
    color: #E2E8F0;
    selection-background-color: #0F52BA;
    selection-color: #FFFFFF;
}

QHeaderView::section {
    background-color: #1A2234;
    color: #94A3B8;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid #26334D;
    padding: 8px 10px;
}

QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #1E293B;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #2A364F;
    background-color: #1A2234;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #121824;
    color: #94A3B8;
    border: 1px solid #2A364F;
    border-bottom: none;
    padding: 8px 16px;
    margin-left: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #1A2234;
    color: #38BDF8;
    font-weight: bold;
    border-bottom: 2px solid #38BDF8;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #121824;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
