from __future__ import annotations

from functools import wraps
from inspect import iscoroutinefunction

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.identity import AuthenticatedUser, IdentityAgent
from app.agents.rbac import RBACAgent
from app.core.database import get_db
from app.core.errors import raise_error
from app.core.security import decode_jwt_token

identity_agent = IdentityAgent()
rbac_agent = RBACAgent()


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise_error("AUTH.INVALID_CREDENTIAL", detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_jwt_token(token)
    except ValueError:
        raise_error("AUTH.INVALID_CREDENTIAL", detail="Invalid token")
    if payload.get("type") != "access":
        raise_error("AUTH.INVALID_CREDENTIAL", detail="Access token required")
    user_id = payload.get("sub")
    if not user_id:
        raise_error("AUTH.INVALID_CREDENTIAL")
    return await identity_agent.load_user(db, int(user_id))


def require_authenticated_user(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    return user


def require_permission(resource: str, action: str, namespace: str | None = "system"):
    async def dependency(
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if not await rbac_agent.is_allowed(user, resource, action, namespace=namespace):
            raise_error("AUTH.FORBIDDEN")
        return user

    return dependency


def permission_guard(resource: str, action: str, namespace: str | None = "system"):
    return Depends(require_permission(resource, action, namespace))


def permission_required(resource: str, action: str, namespace: str | None = "system"):
    guard = permission_guard(resource, action, namespace)

    def decorator(func):
        if iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, __permission=guard, **kwargs):  # type: ignore[misc]
                return await func(*args, **kwargs)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, __permission=guard, **kwargs):  # type: ignore[misc]
            return func(*args, **kwargs)

        return sync_wrapper

    return decorator


async def ensure_permission(
    user: AuthenticatedUser, resource: str, action: str, namespace: str | None = "system"
) -> None:
    if not await rbac_agent.is_allowed(user, resource, action, namespace=namespace):
        raise_error("AUTH.FORBIDDEN")
