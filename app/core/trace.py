from __future__ import annotations

import uuid
from contextvars import ContextVar, Token

_trace_id_ctx: ContextVar[str | None] = ContextVar("trace_id", default=None)


def bind_trace_id(trace_id: str | None = None) -> Token:
    value = trace_id or uuid.uuid4().hex
    return _trace_id_ctx.set(value)


def reset_trace_id(token: Token | None) -> None:
    if token is None:
        return
    _trace_id_ctx.reset(token)


def get_trace_id() -> str:
    trace_id = _trace_id_ctx.get()
    if trace_id:
        return trace_id
    trace_id = uuid.uuid4().hex
    _trace_id_ctx.set(trace_id)
    return trace_id
