"""Structured logging configuration (no secrets, no flags, ever)."""

from __future__ import annotations

import logging
import sys

from app.config import settings

#: Substrings that must never reach a log line.
_REDACTED_MARKERS = ("flag", "password", "token", "secret", "authorization", "apikey")


class RedactingFilter(logging.Filter):
    """Defence-in-depth: scrub obviously sensitive values from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # pragma: no cover - malformed record
            return True
        lowered = message.lower()
        if any(marker in lowered for marker in _REDACTED_MARKERS):
            record.msg = "[redacted log line containing sensitive keyword]"
            record.args = ()
        return True


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    handler.addFilter(RedactingFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    for noisy in ("uvicorn.access", "httpx", "httpcore", "python_multipart"):
        logging.getLogger(noisy).setLevel(max(level, logging.WARNING))

    logging.getLogger("wano").setLevel(level)
