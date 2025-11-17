import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agents.audit import get_audit_agent
from app.core.settings import get_settings
from app.core.trace import get_trace_id
from app.middleware.auth import AuthMiddleware
from app.middleware.trace import TraceMiddleware
from app.routers import auth, audit, user, menu, role, department


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
    app.add_middleware(TraceMiddleware)
    app.add_middleware(AuthMiddleware)

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(user.router, prefix="/users", tags=["users"])
    app.include_router(menu.router, prefix="/menus", tags=["menus"])
    app.include_router(role.router, prefix="/roles", tags=["roles"])
    app.include_router(department.router, prefix="/departments", tags=["departments"])
    app.include_router(audit.router, prefix="/audit", tags=["audit"])

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        # 记录异常审计日志（仅记录服务器错误和权限错误）
        if exc.status_code >= 500 or exc.status_code == 403:
            audit_agent = get_audit_agent()
            operator_id = getattr(request.state, "user_id", None)
            operator_name = getattr(request.state, "username", None)
            await audit_agent.log_event(
                action="HTTP_EXCEPTION",
                resource_type="SYSTEM",
                resource_id=None,
                operator_id=operator_id,
                operator_name=operator_name,
                params={
                    "status_code": exc.status_code,
                    "path": request.url.path,
                    "method": request.method,
                    "detail": detail,
                },
                result_status=False,
                result_message=f"HTTP {exc.status_code}: {detail}",
                request=request,
            )
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
        # 记录未捕获的异常
        audit_agent = get_audit_agent()
        operator_id = getattr(request.state, "user_id", None)
        operator_name = getattr(request.state, "username", None)
        error_trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        await audit_agent.log_event(
            action="UNHANDLED_EXCEPTION",
            resource_type="SYSTEM",
            resource_id=None,
            operator_id=operator_id,
            operator_name=operator_name,
            params={
                "exception_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method,
                "trace_id": get_trace_id(),
            },
            result_status=False,
            result_message=f"{type(exc).__name__}: {str(exc)}",
            request=request,
        )
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "Internal Server Error", "data": None},
        )

    return app


app = create_app()
