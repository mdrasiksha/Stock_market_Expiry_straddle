"""Shared utility helpers."""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


def retry(operation: Callable[[], T], attempts: int = 3, delay: float = 0.5) -> T:
    """Retry transient API calls with linear backoff."""
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:  # broker/API exceptions vary by vendor
            last_error = exc
            logger.warning("Attempt %s/%s failed: %s", attempt, attempts, exc)
            time.sleep(delay * attempt)
    raise RuntimeError("Retry attempts exhausted") from last_error
