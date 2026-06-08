"""
Insurance Claim Pre-Assurance – Structured JSON Logging Configuration
Outputs structured logs to stdout (container-friendly) and a rotating file.
"""
import logging
import logging.handlers
import json
from datetime import datetime, timezone
from pathlib import Path
from app.core.config import settings


class _JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Attach any extra fields passed via extra={} kwarg
        for key, value in record.__dict__.items():
            if key not in (
                "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno",
                "funcName", "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "name", "message",
            ):
                log_entry[key] = value
        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    """Initialise root logger with JSON formatting for all handlers."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    formatter = _JsonFormatter()

    # Stdout handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Rotating file handler (10 MB per file, keep 5 backups)
    log_file = settings.LOG_DIR / "claimsense.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=log_level, handlers=[stream_handler, file_handler])

    # Suppress noisy third-party loggers
    for noisy in ("uvicorn.access", "multipart"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
