from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.settings import get_settings
from app.routers import auth, user, menu, role, department


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="FastAPI Admin Service",
        version="0.1.0",
        summary="Agent-Oriented authentication and authorization backend",
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(user.router, prefix="/users", tags=["users"])
    app.include_router(menu.router, prefix="/menus", tags=["menus"])
    app.include_router(menu.legacy_router, tags=["menu"])
    app.include_router(role.router, prefix="/roles", tags=["roles"])
    app.include_router(role.legacy_router, tags=["role"])
    app.include_router(department.router, prefix="/departments", tags=["departments"])
    app.include_router(department.legacy_router, tags=["department"])

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=200,
            content={"code": exc.status_code, "message": detail, "data": None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={"code": 422, "message": exc.errors(), "data": None},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "Internal Server Error", "data": None},
        )

    return app


app = create_app()
