from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.types import jsonb


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    ip: Mapped[str | None] = mapped_column(String(64))
    ua: Mapped[str | None] = mapped_column(String(255))
    resource: Mapped[str | None] = mapped_column(String(128))
    action: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str | None] = mapped_column(String(32))
    detail: Mapped[dict | None] = mapped_column(jsonb)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
