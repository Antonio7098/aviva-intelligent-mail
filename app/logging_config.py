import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        correlation_id_var.set(correlation_id)

        response = Response(content="", status_code=200)
        response.headers["X-Correlation-ID"] = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class SafeLogger:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, str):
            return "[REDACTED]"
        elif isinstance(value, dict):
            return {k: self._sanitize(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [self._sanitize(item) for item in value]
        return value

    def debug(self, message: str, **kwargs: Any) -> None:
        sanitized_kwargs = {k: self._sanitize(v) for k, v in kwargs.items()}
        extra = {"correlation_id": correlation_id_var.get()}
        self._logger.debug(message, **sanitized_kwargs, extra=extra)

    def info(self, message: str, **kwargs: Any) -> None:
        sanitized_kwargs = {k: self._sanitize(v) for k, v in kwargs.items()}
        extra = {"correlation_id": correlation_id_var.get()}
        self._logger.info(message, **sanitized_kwargs, extra=extra)

    def warning(self, message: str, **kwargs: Any) -> None:
        sanitized_kwargs = {k: self._sanitize(v) for k, v in kwargs.items()}
        extra = {"correlation_id": correlation_id_var.get()}
        self._logger.warning(message, **sanitized_kwargs, extra=extra)

    def error(self, message: str, **kwargs: Any) -> None:
        sanitized_kwargs = {k: self._sanitize(v) for k, v in kwargs.items()}
        extra = {"correlation_id": correlation_id_var.get()}
        self._logger.error(message, **sanitized_kwargs, extra=extra)


def setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format='{"time": "%(asctime)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "message": "%(message)s"}',
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )

    for logger_name in ["uvicorn", "uvicorn.access"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)


def get_logger(name: str) -> SafeLogger:
    return SafeLogger(logging.getLogger(name))
