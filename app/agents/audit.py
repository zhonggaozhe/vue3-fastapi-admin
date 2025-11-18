from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi import Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import AsyncSessionLocal
from app.core.trace import get_trace_id
from app.models.audit import AuditLog

JSONValue = dict[str, Any] | list[Any] | str | int | float | bool | None


class AuditAgent:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or AsyncSessionLocal

    def configure_session_factory(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def log_event(
        self,
        *,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        operator_id: int | None = None,
        operator_name: str | None = None,
        before_state: JSONValue | None = None,
        after_state: JSONValue | None = None,
        params: JSONValue | None = None,
        result_status: bool = True,
        result_message: str | None = None,
        trace_id: str | None = None,
        request_ip: str | None = None,
        user_agent: str | None = None,
        request: Request | None = None,
        db: AsyncSession | None = None,
    ) -> None:
        resolved_trace_id = (
            trace_id
            or (getattr(request.state, "trace_id", None) if request else None)
            or get_trace_id()
        )
        ip = request_ip or (self._extract_ip(request) if request else None)
        ua = user_agent or (request.headers.get("User-Agent") if request else None)
        safe_message = result_message
        if safe_message and len(safe_message) > 480:
            safe_message = f"{safe_message[:477]}..."
        record = {
            "trace_id": resolved_trace_id,
            "operator_id": operator_id,
            "operator_name": operator_name,
            "action": action.upper(),
            "resource_type": resource_type,
            "resource_id": resource_id,
            "request_ip": ip,
            "user_agent": ua,
            "before_state": self._ensure_json(before_state),
            "after_state": self._ensure_json(after_state),
            "params": self._ensure_json(params),
            "result_status": 1 if result_status else 0,
            "result_message": safe_message,
        }
        if db is not None:
            db.add(AuditLog(**record))
            await db.commit()
            return
        await self._schedule_persistence(record)

    async def _schedule_persistence(self, record: dict[str, Any]) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            await self._persist_with_new_session(record)
            return
        loop.create_task(self._persist_with_new_session(record))

    async def _persist_with_new_session(self, record: dict[str, Any]) -> None:
        async with self._session_factory() as session:
            session.add(AuditLog(**record))
            await session.commit()

    @staticmethod
    def _extract_ip(request: Request | None) -> str | None:
        if not request:
            return None
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        if request.client and request.client.host:
            return request.client.host
        return None

    @staticmethod
    def _ensure_json(value: JSONValue | BaseModel | Any) -> JSONValue:
        if value is None:
            return None
        if isinstance(value, BaseModel):
            return value.model_dump(exclude_none=True)
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [AuditAgent._ensure_json(item) for item in value]
        if isinstance(value, dict):
            return {key: AuditAgent._ensure_json(item) for key, item in value.items()}
        try:
            return json.loads(json.dumps(value, default=str))
        except (TypeError, ValueError):
            return str(value)


_audit_agent = AuditAgent()


def get_audit_agent() -> AuditAgent:
    return _audit_agent
