"""
Logging System Module
Provides thread-safe in-memory buffer logging for the Streamlit UI
and file-based logging for auditing and production debugging.
"""

from collections import deque
from datetime import datetime
import logging
import os
from typing import List, Optional

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "scraper.log")


class InMemoryLogHandler(logging.Handler):
    """Custom logging handler that buffers the latest log messages for UI display."""

    def __init__(self, capacity: int = 300):
        super().__init__()
        self.buffer = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.buffer.append({
                "timestamp": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
                "level": record.levelname,
                "message": record.getMessage(),
                "formatted": msg,
            })
        except Exception:
            self.handleError(record)

    def get_logs(self) -> List[dict]:
        return list(self.buffer)

    def clear(self):
        self.buffer.clear()


# Global in-memory handler instance
_memory_handler: Optional[InMemoryLogHandler] = None


def setup_logger(log_level: int = logging.INFO) -> logging.Logger:
    """Configure and return the application-wide root logger."""
    global _memory_handler

    logger = logging.getLogger("scraper")
    logger.setLevel(log_level)

    # Prevent adding handlers repeatedly if already configured
    if logger.handlers:
        return logger

    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. File Handler
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as exc:
        print(f"Warning: Could not initialize log file at {LOG_FILE}: {exc}")

    # 2. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 3. In-Memory Handler for Streamlit Dashboard
    _memory_handler = InMemoryLogHandler(capacity=500)
    _memory_handler.setLevel(log_level)
    _memory_handler.setFormatter(formatter)
    logger.addHandler(_memory_handler)

    return logger


def get_logs_for_ui() -> List[dict]:
    """Retrieve all log events currently stored in the memory buffer."""
    if _memory_handler:
        return _memory_handler.get_logs()
    return []


def clear_ui_logs():
    """Clear the memory buffer."""
    if _memory_handler:
        _memory_handler.clear()
