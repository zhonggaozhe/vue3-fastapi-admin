from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import raise_error
from app.core.security import verify_password
from app.core.settings import get_settings
from app.models.role import Role, Permission
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest


@dataclass(slots=True)
class RoleInfo:
    id: int
    code: str
    name: str


@dataclass(slots=True)
class AuthenticatedUser:
    id: int
    username: str
    email: str | None
    full_name: str | None
    roles: list[RoleInfo]
    permissions: list[str]
    attributes: dict[str, Any]
    is_superuser: bool

    @property
    def primary_role(self) -> RoleInfo | None:
        return self.roles[0] if self.roles else None


class IdentityAgent:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def authenticate(
        self, db: AsyncSession, redis: Redis, payload: LoginRequest
    ) -> AuthenticatedUser:
        repo = UserRepository(db)
        user = await repo.get_by_username(payload.username)
        if not user or not user.is_active:
            raise_error("AUTH.INVALID_CREDENTIAL")
        await self._ensure_not_locked(db, user)
        if not verify_password(payload.password, user.password_hash):
            await self._record_failed_attempt(db, redis, user)
        await self._reset_failures(redis, user.id)
        return self._map_user(user)

    async def load_user(self, db: AsyncSession, user_id: int) -> AuthenticatedUser:
        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise_error("AUTH.INVALID_CREDENTIAL")
        return self._map_user(user)

    def _map_user(self, user: User) -> AuthenticatedUser:
        roles = [RoleInfo(id=role.id, code=role.code, name=role.name) for role in user.roles]
        permissions = sorted({self._permission_value(perm) for role in user.roles for perm in role.permissions})
        return AuthenticatedUser(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=roles,
            permissions=permissions,
            attributes=user.attributes or {},
            is_superuser=user.is_superuser,
        )

    @staticmethod
    def _permission_value(permission: Permission) -> str:
        namespace = (permission.namespace or "").strip()
        resource = permission.resource.strip()
        action = permission.action.strip()
        if namespace == resource == action == "*":
            return "*.*.*"
        if namespace:
            return f"{namespace}:{resource}:{action}"
        return f"{resource}:{action}"

    async def _ensure_not_locked(self, db: AsyncSession, user: User) -> None:
        if not user.locked_until:
            return
        now = datetime.now(timezone.utc)
        if user.locked_until > now:
            remaining_minutes = max(
                1, int((user.locked_until - now).total_seconds() // 60) or 1
            )
            raise_error(
                "AUTH.ACCOUNT_LOCKED",
                detail=f"Account locked. Try again in {remaining_minutes} minute(s).",
            )
        user.locked_until = None
        await db.commit()

    async def _record_failed_attempt(self, db: AsyncSession, redis: Redis, user: User) -> None:
        key = self._failure_counter_key(user.id)
        attempts = await redis.incr(key)
        if attempts == 1:
            await redis.expire(key, self.settings.login_failure_window_minutes * 60)
        if attempts >= self.settings.login_failure_limit:
            await redis.delete(key)
            await self._lock_account(db, user)
            raise_error("AUTH.ACCOUNT_LOCKED", detail="Account locked due to repeated failures")
        raise_error("AUTH.INVALID_CREDENTIAL")

    async def _lock_account(self, db: AsyncSession, user: User) -> None:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=self.settings.login_lock_minutes)
        await db.commit()

    def _failure_counter_key(self, user_id: int) -> str:
        return f"auth:fail:{user_id}"

    async def _reset_failures(self, redis: Redis, user_id: int) -> None:
        await redis.delete(self._failure_counter_key(user_id))
