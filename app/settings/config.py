import os
import typing
import warnings

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VERSION: str = "0.1.0"
    APP_TITLE: str = "Vue FastAPI Admin"
    PROJECT_NAME: str = "Vue FastAPI Admin"
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: typing.List = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]
    TORTOISE_ORM: dict = {}

    DEBUG: bool = True

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(PROJECT_ROOT, "log")
    SECRET_KEY: str = "3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    DB_CONNECTION: str = os.getenv("DB_CONNECTION", "postgres")
    SQLITE_DB_PATH: str = os.path.join(BASE_DIR, "db.sqlite3")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5433"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "pcpNeCHcT83AGs6xhWv6")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "fastapi_admin_db")

    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    def build_tortoise_config(self) -> dict:
        connections: dict[str, dict] = {
            "sqlite": {
                "engine": "tortoise.backends.sqlite",
                "credentials": {"file_path": self.SQLITE_DB_PATH},
            }
        }

        if self.DB_CONNECTION == "postgres":
            try:
                import asyncpg  # noqa: F401
            except ImportError:
                warnings.warn(
                    "未检测到 asyncpg，已自动回落至 sqlite。若需连接 Postgres，请先安装 tortoise-orm[asyncpg]。",
                    RuntimeWarning,
                )
                self.DB_CONNECTION = "sqlite"
            else:
                connections["postgres"] = {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": self.POSTGRES_HOST,
                        "port": self.POSTGRES_PORT,
                        "user": self.POSTGRES_USER,
                        "password": self.POSTGRES_PASSWORD,
                        "database": self.POSTGRES_DB,
                    },
                }

        default_conn = self.DB_CONNECTION if self.DB_CONNECTION in connections else "sqlite"
        return {
            "connections": connections,
            "apps": {
                "models": {
                    "models": ["app.models", "aerich.models"],
                    "default_connection": self.DB_CONNECTION,
                },
            },
            "use_tz": False,
            "timezone": "Asia/Shanghai",
        }


settings = Settings()
settings.TORTOISE_ORM = settings.build_tortoise_config()
