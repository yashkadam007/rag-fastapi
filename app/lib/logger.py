from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import Request

from app import config


def get_logger(name: str = "rag") -> logging.Logger:
    """Create or get a configured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


async def request_logging_middleware(request: Request, call_next: Callable):
    """Log request method, path, status, and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000.0
    logger = get_logger("rag.request")
    logger.info(
        "%s %s -> %s in %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response
