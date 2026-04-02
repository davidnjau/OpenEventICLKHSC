"""
Logging configuration for the Intellisoft Middleware.

Outputs:
  - Coloured console output (human-readable during development)
  - Rotating file log at logs/middleware.log  (max 10 MB × 5 backups)

Log format:
  2026-04-02 10:23:45.123 | INFO     | app.routes.import_:import_delegates:42 | Imported 5 delegates
"""

import logging
import logging.handlers
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "middleware.log"

# --------------------------------------------------------------------------- #
# Formatter                                                                     #
# --------------------------------------------------------------------------- #

_FMT = "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

# ANSI colour codes for console output
_COLOURS = {
    "DEBUG":    "\033[36m",   # Cyan
    "INFO":     "\033[32m",   # Green
    "WARNING":  "\033[33m",   # Yellow
    "ERROR":    "\033[31m",   # Red
    "CRITICAL": "\033[41m",   # Red background
}
_RESET = "\033[0m"


class _ColouredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, "")
        record.levelname = f"{colour}{record.levelname}{_RESET}"
        return super().format(record)


# --------------------------------------------------------------------------- #
# Public helper                                                                 #
# --------------------------------------------------------------------------- #

def setup_logging(level: str = "INFO") -> None:
    """
    Call once at application startup.  All subsequent ``getLogger`` calls
    automatically inherit this configuration.
    """
    root = logging.getLogger()
    root.setLevel(level.upper())

    # 1. Console handler — coloured, goes to stdout
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(_ColouredFormatter(_FMT, datefmt=_DATE_FMT))
    console.setLevel(level.upper())

    # 2. Rotating file handler — plain text, no colours
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,   # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
    file_handler.setLevel("DEBUG")   # always capture everything to disk

    # Avoid duplicate handlers if called more than once (e.g. in tests)
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(file_handler)

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Convenience wrapper — same as ``logging.getLogger(name)``."""
    return logging.getLogger(name)
