"""
Application lifecycle manager for startup initialization and graceful shutdown.
"""
from typing import Callable
from app.config.settings import settings
from app.core.logger import app_logger
from app.core.offline_guard import enforce_offline_mode

_SHUTDOWN_HOOKS: list[Callable[[], None]] = []


def initialize_application() -> None:
    """Bootstraps application state, directories, storage, and safety guards."""
    app_logger.info("Initializing Sepehryar AI Engine (v%s)...", settings.app_version)

    # 1. Ensure system directories exist
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    settings.knowledge_path.mkdir(parents=True, exist_ok=True)

    # 2. Strict Offline Guard enforcement
    if settings.offline_strict:
        enforce_offline_mode()

    # 3. Initialize SQLite Storage Schema
    try:
        from app.storage.repository import storage_repo
        storage_repo.initialize_database()
        app_logger.info("Local SQLite storage initialized successfully at %s", settings.sqlite_db_path)
    except Exception as e:
        app_logger.critical("Failed to initialize SQLite storage: %s", e)
        raise

    # 4. Synchronize Offline Knowledge Base
    try:
        from app.knowledge.indexer import knowledge_indexer
        k_stats = knowledge_indexer.index_directory()
        app_logger.info("Knowledge base synchronized: %d indexed, %d skipped (%d total chunks)",
                        k_stats["indexed"], k_stats["skipped"], k_stats["total_chunks"])
    except Exception as e:
        app_logger.warning("Knowledge base sync warning: %s", e)

    app_logger.info("Initialization complete. Running in mode: %s", settings.app_env)


def register_shutdown_hook(callback: Callable[[], None]) -> None:
    """Register cleanup callback for application shutdown."""
    _SHUTDOWN_HOOKS.append(callback)


def shutdown_application() -> None:
    """Execute registered cleanup callbacks before exit."""
    app_logger.info("Shutting down Sepehryar AI Engine...")
    for hook in _SHUTDOWN_HOOKS:
        try:
            hook()
        except Exception as e:
            app_logger.error("Error executing shutdown hook: %s", e)
    app_logger.info("Shutdown sequence completed.")
