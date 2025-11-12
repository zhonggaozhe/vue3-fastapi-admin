from fastapi import FastAPI

from app.core.settings import get_settings
from app.routers import auth, user, menu


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="FastAPI Admin Service",
        version="0.1.0",
        summary="Agent-Oriented authentication and authorization backend",
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
    )

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(user.router, prefix="/users", tags=["users"])
    app.include_router(menu.router, prefix="/menus", tags=["menus"])

    return app


app = create_app()
