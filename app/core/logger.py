"""
Multi-channel logging system with automatic credential and sensitive data scrubbing.
Channels:
  1. app_logger: General application runtime events (logs/app.log)
  2. ai_logger: AI orchestration, reasoning, tool execution (logs/ai.log)
  3. audit_logger: Structured security and operational audit trail (logs/audit.log)
"""
import re
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from app.config.settings import settings

# Sensitive keyword patterns for automated scrubbing in logs
SENSITIVE_PATTERNS = [
    (re.compile(r'(?i)(password|pwd|pass)\s*=\s*([^\s;,\'\"]+)', re.IGNORECASE), r'\1=[PROTECTED]'),
    (re.compile(r'(?i)(api[_-]?token|secret|access[_-]?key)\s*[:=]\s*([^\s;,\'\"]+)', re.IGNORECASE), r'\1=[PROTECTED]'),
    (re.compile(r'(?i)(bearer\s+)([a-zA-Z0-9_\-\.]+)', re.IGNORECASE), r'\1[PROTECTED]'),
]


def scrub_credentials(text: str) -> str:
    """Mask passwords and tokens from string before outputting to logs."""
    if not isinstance(text, str):
        text = str(text)
    scrubbed = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        scrubbed = pattern.sub(replacement, scrubbed)
    return scrubbed


class SafeScrubbingFormatter(logging.Formatter):
    """Logging formatter that scrubs sensitive credentials from record messages."""
    def format(self, record: logging.LogRecord) -> str:
        # Scrub message
        original_msg = record.msg
        if isinstance(record.msg, str):
            record.msg = scrub_credentials(record.msg)
        elif hasattr(record, "args") and record.args:
            # If formatted with % args
            record.msg = scrub_credentials(str(record.msg))

        formatted = super().format(record)
        record.msg = original_msg  # restore original message
        return scrub_credentials(formatted)


def setup_loggers() -> tuple[logging.Logger, logging.Logger, logging.Logger]:
    """Configure and return app_logger, ai_logger, audit_logger."""
    log_dir = settings.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Common formatter
    std_formatter = SafeScrubbingFormatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Root / Application Logger
    app_logger = logging.getLogger("sepehryar.app")
    app_logger.setLevel(log_level)
    if not app_logger.handlers:
        # File handler (Rotating 10MB x 5 backups)
        app_file_handler = RotatingFileHandler(
            settings.log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        app_file_handler.setFormatter(std_formatter)
        app_logger.addHandler(app_file_handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(std_formatter)
        app_logger.addHandler(console_handler)

    # 2. AI Logger
    ai_logger = logging.getLogger("sepehryar.ai")
    ai_logger.setLevel(log_level)
    if not ai_logger.handlers:
        ai_file_handler = RotatingFileHandler(
            settings.ai_log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        ai_file_handler.setFormatter(std_formatter)
        ai_logger.addHandler(ai_file_handler)

    # 3. Audit Logger (JSON/Structured log)
    audit_logger = logging.getLogger("sepehryar.audit")
    audit_logger.setLevel(logging.INFO)
    if not audit_logger.handlers:
        audit_file_handler = RotatingFileHandler(
            settings.audit_log_path,
            maxBytes=20 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8"
        )
        audit_formatter = SafeScrubbingFormatter(
            fmt="%(asctime)s | AUDIT | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        audit_file_handler.setFormatter(audit_formatter)
        audit_logger.addHandler(audit_file_handler)

    return app_logger, ai_logger, audit_logger


# Global instances
app_logger, ai_logger, audit_logger = setup_loggers()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get child logger with scrubbing capabilities."""
    if not name:
        return app_logger
    return logging.getLogger(f"sepehryar.{name}")
