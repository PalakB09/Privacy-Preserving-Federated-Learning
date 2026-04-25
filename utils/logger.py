"""
Structured Logger

Provides timestamped, module-tagged, color-coded console output
for clean simulation logs suitable for academic demos.
"""

import logging
import sys
from datetime import datetime


class _ColorFormatter(logging.Formatter):
    """ANSI-colored formatter keyed on log level."""

    COLORS = {
        logging.DEBUG: "\033[90m",      # grey
        logging.INFO: "\033[36m",       # cyan
        logging.WARNING: "\033[33m",    # yellow
        logging.ERROR: "\033[31m",      # red
        logging.CRITICAL: "\033[1;31m", # bold red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        timestamp = datetime.now().strftime("%H:%M:%S")
        module = record.name
        msg = record.getMessage()
        return f"{color}[{timestamp}] [{module}]{self.RESET} {msg}"


def get_logger(module_name: str) -> logging.Logger:
    """
    Return a configured logger for the given module.

    All loggers share a single StreamHandler so output stays clean
    even when multiple modules log simultaneously.
    """
    logger = logging.getLogger(f"threshold-fl.{module_name}")

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_ColorFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger
