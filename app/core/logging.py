from __future__ import annotations

import json
import logging
import sys
from typing import Any, Mapping

from app.core.trace import get_trace_id

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] trace_id=%(trace_id)s %(message)s"
DEFAULT_LOG_LEVEL = logging.INFO


class TraceFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        if not hasattr(record, "trace_id"):
            record.trace_id = get_trace_id()
        return super().format(record)


def configure_logging(level: str | int = DEFAULT_LOG_LEVEL) -> None:
    """Configure the root logger once with a predictable format."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(TraceFormatter(DEFAULT_LOG_FORMAT))
    logging.basicConfig(
        level=_resolve_level(level),
        handlers=[handler],
    )


class StructuredLogger:
    """Lightweight wrapper around logging.Logger that injects trace ids and context."""

    def __init__(
        self, logger: logging.Logger, bound_context: Mapping[str, Any] | None = None
    ) -> None:
        self._logger = logger
        self._context = dict(bound_context or {})

    def bind(self, **context: Any) -> "StructuredLogger":
        """Bind static context that will be appended to every log message."""
        if not context:
            return self
        return StructuredLogger(self._logger, {**self._context, **context})

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, args, kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, args, kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, args, kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, args, kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, msg, args, kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        kwargs["exc_info"] = kwargs.get("exc_info", True)
        self._log(logging.ERROR, msg, args, kwargs)

    def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(level, msg, args, kwargs)

    def _log(self, level: int, msg: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        if not self._logger.isEnabledFor(level):
            return
        kwargs = dict(kwargs)
        extra = kwargs.pop("extra", None) or {}
        context = kwargs.pop("context", None)
        merged_context = dict(self._context)
        if isinstance(context, Mapping):
            merged_context.update(context)
        elif context is not None:
            merged_context["data"] = context
        formatted_message = msg
        if merged_context:
            formatted_message = f"{msg} | context={self._serialize(merged_context)}"
        formatted_message = self._format_message(formatted_message, args)
        extra_with_trace = {**extra, "trace_id": get_trace_id()}
        self._logger.log(level, formatted_message, extra=extra_with_trace, **kwargs)

    @staticmethod
    def _serialize(value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _format_message(message: str, args: tuple[Any, ...]) -> str:
        if not args:
            return message
        try:
            return message % args
        except TypeError:
            joined_args = " ".join(str(arg) for arg in args)
            return f"{message} | args={joined_args}"


def get_logger(name: str | None = None) -> StructuredLogger:
    configure_logging()
    base_logger = logging.getLogger(name or "app")
    return StructuredLogger(base_logger)


def _resolve_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), None)
        if isinstance(numeric_level, int):
            return numeric_level
    return DEFAULT_LOG_LEVEL
