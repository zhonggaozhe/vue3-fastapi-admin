from typing import Any

from pydantic import BaseModel


def success_response(data: Any = None) -> dict[str, Any]:
    if isinstance(data, BaseModel):
        return {"code": 0, "data": data.model_dump(by_alias=True)}
    return {"code": 0, "data": data}

