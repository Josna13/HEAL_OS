"""
HealOS 2.0 - Core System, Error, and Event Logger
Provides thread-safe logging facilities using RotatingFileHandler.
Guarantees idempotency to prevent duplicate log handlers.
"""

import logging
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config import (
    SYSTEM_LOG_FILE,
    ERROR_LOG_FILE,
    EVENTS_LOG_FILE,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT,
)

# Global lock for thread-safe logger initialization
_LOGGER_LOCK = threading.Lock()
_INITIALIZED_LOGGERS = set()


def _configure_rotating_file_logger(
    logger_name: str,
    log_file: Path,
    level: int = logging.INFO,
    formatter: Optional[logging.Formatter] = None,
) -> logging.Logger:
    """
    Configures and returns a named logger with a RotatingFileHandler.
    Prevents adding duplicate handlers on repeated calls.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    with _LOGGER_LOCK:
        if logger_name in _INITIALIZED_LOGGERS:
            return logger

        log_file.parent.mkdir(parents=True, exist_ok=True)

        if formatter is None:
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [%(name)s] [%(threadName)s]: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(formatter)
        handler.setLevel(level)

        # Clear existing handlers if any to prevent duplicates
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.propagate = False

        _INITIALIZED_LOGGERS.add(logger_name)

    return logger


def get_system_logger() -> logging.Logger:
    """Returns the central system logger writing to logs/system.log."""
    return _configure_rotating_file_logger("healos.system", SYSTEM_LOG_FILE, logging.INFO)


def get_error_logger() -> logging.Logger:
    """Returns the dedicated error logger writing to logs/error.log."""
    return _configure_rotating_file_logger("healos.error", ERROR_LOG_FILE, logging.WARNING)


def get_event_logger() -> logging.Logger:
    """Returns the timeline event logger writing to logs/events.log."""
    event_formatter = logging.Formatter(
        fmt="%(asctime)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return _configure_rotating_file_logger(
        "healos.events", EVENTS_LOG_FILE, logging.INFO, formatter=event_formatter
    )


def log_event(message: str) -> None:
    """Convenience helper to record an entry in the events log."""
    event_logger = get_event_logger()
    event_logger.info(message)
