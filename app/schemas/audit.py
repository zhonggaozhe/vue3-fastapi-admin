from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditLogRead(BaseModel):
    id: int
    trace_id: str
    operator_id: int | None = None
    operator_name: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    request_ip: str | None = None
    user_agent: str | None = None
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None
    params: dict[str, Any] | None = None
    result_status: int
    result_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogQuery(BaseModel):
    operator_id: int | None = None
    operator_name: str | None = None
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    result_status: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class AuditLogListResponse(BaseModel):
    list: list[AuditLogRead]
    total: int
    page: int
    page_size: int

