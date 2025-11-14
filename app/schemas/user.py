from pydantic import BaseModel, EmailStr, Field


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


class DepartmentRef(BaseModel):
    id: int | str


class UserCreatePayload(BaseModel):
    username: str
    account: str
    email: EmailStr | None = None
    department: DepartmentRef | None = None
    role: list[int] = Field(default_factory=list)
    password: str | None = None


class UserUpdatePayload(UserCreatePayload):
    id: int


class UserSavePayload(UserCreatePayload):
    id: int | None = None


class UserDeletePayload(BaseModel):
    ids: list[int]
