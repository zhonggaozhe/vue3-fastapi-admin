from dataclasses import dataclass

from app.core.security import create_jwt_token
from app.core.settings import get_settings
from app.agents.identity import AuthenticatedUser

settings = get_settings()


@dataclass(slots=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int
    access_payload: dict
    refresh_payload: dict


class TokenAgent:
    async def issue_pair(self, user: AuthenticatedUser, device_id: str | None = None) -> IssuedTokens:
        primary_role = user.primary_role
        access = create_jwt_token(
            sub=str(user.id),
            expires_minutes=settings.access_token_ttl_minutes,
            token_type="access",
            role=primary_role.code if primary_role else "",
            role_id=str(primary_role.id) if primary_role else "",
            permissions=user.permissions,
            device_id=device_id,
        )
        refresh = create_jwt_token(
            sub=str(user.id),
            expires_minutes=settings.refresh_token_ttl_minutes,
            token_type="refresh",
            rotation="single",
            device_id=device_id,
        )
        return IssuedTokens(
            access_token=access["token"],
            refresh_token=refresh["token"],
            expires_in=settings.access_token_ttl_minutes * 60,
            access_payload=access["payload"],
            refresh_payload=refresh["payload"],
        )
