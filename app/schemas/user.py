from pydantic import BaseModel, EmailStr


class RoleBrief(BaseModel):
    id: int
    code: str
    name: str


class UserBase(BaseModel):
    username: str
    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str
    role_ids: list[int] = []


class UserRead(UserBase):
    id: int
    role_ids: list[int] = []
    roles: list[RoleBrief] = []
    permissions: list[str] = []

    class Config:
        from_attributes = True
