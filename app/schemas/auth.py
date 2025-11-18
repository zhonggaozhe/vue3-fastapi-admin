from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str
    mfa_code: str | None = None
    device_id: str | None = None


class TokenPair(BaseModel):
    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    token_type: str = "Bearer"
    expires_in: int
    payload: dict[str, Any]


class SessionInfo(BaseModel):
    sid: str
    expires_at: datetime


class LoginResponse(BaseModel):
    tokens: TokenPair
    session: SessionInfo


class RefreshRequest(BaseModel):
    refresh_token: str = Field(alias="refreshToken")
    device_id: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(default=None, alias="refreshToken")
