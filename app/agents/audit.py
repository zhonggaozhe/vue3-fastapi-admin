from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


class AuditAgent:
    async def log_event(
        self,
        db: AsyncSession,
        *,
        event_type: Literal["login_success", "login_failure", "token_refresh", "logout"],
        user_id: int | None,
        detail: dict | None = None,
    ) -> None:
        log = AuditLog(
            event_type=event_type,
            user_id=user_id,
            status="success",
            detail=detail,
        )
        db.add(log)
        await db.commit()
