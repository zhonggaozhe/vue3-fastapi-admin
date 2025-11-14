from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_jwt_token


class AuthMiddleware(BaseHTTPMiddleware):
    """中间件：从JWT token中提取用户ID并保存到request.state"""

    async def dispatch(self, request: Request, call_next):
        # 尝试从Authorization header中提取用户ID
        authorization = request.headers.get("Authorization")
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]
            try:
                payload = decode_jwt_token(token)
                if payload.get("type") == "access":
                    user_id = payload.get("sub")
                    if user_id:
                        request.state.user_id = int(user_id)
            except (ValueError, KeyError, TypeError):
                # Token无效，忽略
                pass

        response = await call_next(request)
        return response

