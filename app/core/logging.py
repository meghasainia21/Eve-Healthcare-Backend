"""
Lightweight structured logging.

We emit one JSON object per log line so logs are easy to grep/ship to a
log aggregator, without pulling in a heavy logging framework.
"""

import json
import logging
import sys
import time
from typing import Any


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": round(time.time(), 3),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Allow callers to attach extra structured fields via `extra={...}`
        for key, value in record.__dict__.items():
            if key in ("request_id", "path", "method", "status_code", "duration_ms", "user_id"):
                payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging(log_level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Quiet down noisy third-party loggers a little.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
