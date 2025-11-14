from typing import List

from pydantic import BaseModel, ConfigDict, Field


class RoleUpsertBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role_code: str = Field(..., alias="role")
    role_name: str = Field(..., alias="roleName")
    status: int = Field(1, ge=0, le=1)
    remark: str | None = None
    menu_ids: List[int] = Field(default_factory=list, alias="menuIds")


class RoleCreate(RoleUpsertBase):
    pass


class RoleUpdate(RoleUpsertBase):
    pass


class RoleEditPayload(RoleUpsertBase):
    id: int


class RoleDeletePayload(BaseModel):
    ids: List[int]
