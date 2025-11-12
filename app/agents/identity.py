from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import raise_error
from app.core.security import verify_password
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
    async def authenticate(self, db: AsyncSession, payload: LoginRequest) -> AuthenticatedUser:
        repo = UserRepository(db)
        user = await repo.get_by_username(payload.username)
        if not user or not user.is_active:
            raise_error("AUTH.INVALID_CREDENTIAL")
        if not verify_password(payload.password, user.password_hash):
            raise_error("AUTH.INVALID_CREDENTIAL")
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
