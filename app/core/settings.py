from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    app_name: str = "FastAPI Admin Service"
    environment: Literal["local", "dev", "prod"] = "local"
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/admin",
        description="SQLAlchemy async database URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    docs_url: Optional[str] = "/docs"
    redoc_url: Optional[str] = "/redoc"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_minutes: int = 24 * 60
    login_failure_limit: int = Field(
        default=5, description="Consecutive failed attempts allowed before locking the account"
    )
    login_failure_window_minutes: int = Field(
        default=15, description="Time window for counting consecutive login failures"
    )
    login_lock_minutes: int = Field(default=15, description="Account lock duration in minutes")
    jwt_public_key_path: str = "certs/jwt_public.pem"
    jwt_private_key_path: str = "certs/jwt_private.pem"
    jwt_algorithm: str = "HS256"
    jwt_secret_key: str = Field(default="change-me", description="HS* symmetric secret")
    rate_limit_default: int = 100
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:4000",
            "http://127.0.0.1:4000",
        ]
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])
    super_admin_username: str = Field(default="admin", description="Reserved super admin username")
    super_admin_role_code: str = Field(default="admin", description="Reserved super admin role code")


@lru_cache
def get_settings() -> Settings:
    return Settings()
