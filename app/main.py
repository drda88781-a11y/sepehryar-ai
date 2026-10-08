"""
Main application launch module coordinating lifecycle and PySide6 application startup.
"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from app.core.lifecycle import initialize_application, shutdown_application
from app.core.logger import app_logger
from app.ui.main_window import MainWindow


def start_gui() -> int:
    """Launch PySide6 graphical user interface."""
    initialize_application()
    app_logger.info("Starting PySide6 GUI...")

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setApplicationName("Sepehryar AI Engine")

    window = MainWindow()
    window.show()

    exit_code = app.exec()
    shutdown_application()
    return exit_code
