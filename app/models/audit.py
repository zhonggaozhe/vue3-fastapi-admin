from datetime import datetime

from sqlalchemy import DateTime, Index, String, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.types import jsonb


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("idx_audit_log_trace", "trace_id"),
        Index("idx_audit_log_operator", "operator_id"),
        Index("idx_audit_log_action", "action"),
        Index("idx_audit_log_resource", "resource_type", "resource_id"),
        Index("idx_audit_log_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    operator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    operator_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(256), nullable=True)
    before_state: Mapped[dict | None] = mapped_column(jsonb)
    after_state: Mapped[dict | None] = mapped_column(jsonb)
    params: Mapped[dict | None] = mapped_column(jsonb)
    result_status: Mapped[int] = mapped_column(default=1)
    result_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
