from typing import Any

from pydantic import BaseModel


def success_response(data: Any = None, message: str = "") -> dict[str, Any]:
    payload: Any = data
    if isinstance(data, BaseModel):
        payload = data.model_dump(by_alias=True)
    return {"code": 0, "message": message, "data": payload}
