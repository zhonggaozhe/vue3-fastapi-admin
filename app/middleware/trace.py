from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.trace import bind_trace_id, get_trace_id, reset_trace_id


class TraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming_trace = request.headers.get("X-Trace-Id") or request.headers.get("X-Request-Id")
        token = bind_trace_id(incoming_trace)
        trace_id = get_trace_id()
        request.state.trace_id = trace_id
        try:
            response = await call_next(request)
        finally:
            reset_trace_id(token)
        response.headers["X-Trace-Id"] = trace_id
        return response
