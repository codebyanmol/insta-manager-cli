"""
logger.py — Activity Logging Module
=====================================
Handles writing, reading, and clearing the persistent activity log.
All user actions (login, unfollow, export, etc.) are timestamped here.
"""

import logging
from pathlib import Path

LOG_DIR  = Path("logs")
LOG_FILE = LOG_DIR / "instagram_manager.log"


# ─── Internal setup ───────────────────────────────────────────────────────────

def _get_logger() -> logging.Logger:
    """Return (or create) the module-level file logger."""
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger("instagram_manager")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers on repeated calls
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M")
        )
        logger.addHandler(handler)

    return logger


# ─── Public API ───────────────────────────────────────────────────────────────

def log_action(message: str, level: str = "info") -> None:
    """Write *message* to the log file at the given severity level."""
    logger = _get_logger()
    {"info": logger.info, "warning": logger.warning, "error": logger.error}.get(
        level, logger.info
    )(message)


def get_log_lines(max_lines: int = 200) -> list[str]:
    """Return up to *max_lines* recent log lines (newest-last order)."""
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    return lines[-max_lines:]


def clear_logs() -> None:
    """Truncate the log file."""
    LOG_FILE.write_text("", encoding="utf-8")


def log_file_path() -> str:
    """Return the absolute path of the current log file."""
    return str(LOG_FILE.resolve())