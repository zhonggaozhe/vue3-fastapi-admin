from fastapi import HTTPException, status

ERROR_MAP = {
    "AUTH.INVALID_CREDENTIAL": (status.HTTP_401_UNAUTHORIZED, "Invalid username or password"),
    "AUTH.MFA_REQUIRED": (status.HTTP_401_UNAUTHORIZED, "MFA required"),
    "AUTH.TOKEN_EXPIRED": (status.HTTP_401_UNAUTHORIZED, "Token expired"),
    "AUTH.REFRESH_INVALID": (status.HTTP_401_UNAUTHORIZED, "Refresh token invalid"),
    "AUTH.FORBIDDEN": (status.HTTP_403_FORBIDDEN, "Forbidden"),
    "AUTH.RATE_LIMIT": (status.HTTP_429_TOO_MANY_REQUESTS, "Rate limited"),
    "AUTH.ACCOUNT_LOCKED": (status.HTTP_423_LOCKED, "Account is temporarily locked"),
}


def raise_error(code: str, detail: str | None = None) -> None:
    status_code, default_detail = ERROR_MAP.get(code, (status.HTTP_400_BAD_REQUEST, "Bad request"))
    raise HTTPException(status_code=status_code, detail=detail or default_detail)
