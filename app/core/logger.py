import json
import logging
import sys
from typing import Any


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging in production."""

    def format(self, record: logging.LogRecord) -> str:
        """Formats a log record as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            A JSON-formatted log string.
        """
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for development environment."""

    COLORS: dict[int, str] = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[1;31m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Formats a log record with ANSI color codes.

        Args:
            record: The log record to format.

        Returns:
            A color-formatted log string.
        """
        color = self.COLORS.get(record.levelno, self.RESET)
        levelname = f"{color}{record.levelname:<8}{self.RESET}"
        formatted_time = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        message = record.getMessage()
        output = f"{formatted_time} | {levelname} | {record.name} | {message}"
        if record.exc_info and record.exc_info[1] is not None:
            output += f"\n{self.formatException(record.exc_info)}"
        return output


def setup_logger(name: str, level: str = "INFO", structured: bool = False) -> logging.Logger:
    """Creates and configures a logger instance.

    Args:
        name: The logger name, typically the module name.
        level: The log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        structured: If True, uses JSON formatting; otherwise uses colored output.

    Returns:
        A configured Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))

        formatter: logging.Formatter
        if structured:
            formatter = StructuredFormatter()
        else:
            formatter = ColoredFormatter()

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    """Gets or creates a logger with the application's default configuration.

    Args:
        name: The logger name, typically __name__ of the calling module.

    Returns:
        A configured Logger instance.
    """
    from app.core.config import get_settings

    settings = get_settings()
    return setup_logger(name, level=settings.log_level)
