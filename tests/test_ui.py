"""
Unit test for PySide6 GUI window initialization.
"""
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow


def test_main_window_initialization(qapp):
    """Verify MainWindow and its pages instantiate cleanly."""
    window = MainWindow()
    assert window is not None
    assert "Sepehryar" in window.windowTitle()
    assert window.pages_stack.count() == 4
    assert window.spotlight_bar is not None
    assert "chat" in window.pages_map
    assert "integration" in window.pages_map
    assert "docs" in window.pages_map
