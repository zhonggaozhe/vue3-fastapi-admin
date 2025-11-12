from fastapi import APIRouter, Depends, Header
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.audit import AuditAgent
from app.agents.identity import IdentityAgent
from app.agents.orchestrator import AuthOrchestrator
from app.agents.ratelimit import RateLimitAgent
from app.agents.rbac import RBACAgent
from app.agents.session import SessionAgent
from app.agents.token import TokenAgent
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.responses import success_response
from app.core.security import decode_jwt_token
from app.schemas.auth import LoginRequest, LoginResponse, LogoutRequest, RefreshRequest

router = APIRouter()

_orchestrator = AuthOrchestrator(
    identity_agent=IdentityAgent(),
    token_agent=TokenAgent(),
    rbac_agent=RBACAgent(),
    session_agent=SessionAgent(),
    audit_agent=AuditAgent(),
    rate_limit_agent=RateLimitAgent(),
)


def get_orchestrator() -> AuthOrchestrator:
    return _orchestrator


@router.post("/login")
async def login(
    payload: LoginRequest,
    orchestrator: AuthOrchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    result = await orchestrator.login(db, redis, payload)
    return success_response(result)


@router.post("/refresh")
async def refresh(
    payload: RefreshRequest,
    orchestrator: AuthOrchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    result = await orchestrator.refresh(db, redis, payload)
    return success_response(result)


@router.post("/logout")
async def logout(
    _: LogoutRequest,
    authorization: str | None = Header(default=None),
    orchestrator: AuthOrchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    sub = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            sub = decode_jwt_token(token).get("sub")
        except ValueError:
            sub = None
    result = await orchestrator.logout(db, redis, sub)
    return success_response(result)
