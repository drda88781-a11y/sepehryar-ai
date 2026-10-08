"""
Pytest fixtures and environment configuration.
"""
import pytest
from pathlib import Path
from app.config.settings import settings
from app.core.lifecycle import initialize_application
from app.storage.repository import storage_repo


from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure system directories, logging, and storage tables are prepared."""
    settings.offline_strict = False  # Avoid socket patch collisions during tests unless testing offline_guard
    initialize_application()
    yield

@pytest.fixture(scope="session")
def qapp():
    """QApplication fixture for offscreen UI testing."""
    app = QApplication.instance()
    if app is None:
        import sys
        app = QApplication(sys.argv)
    yield app
