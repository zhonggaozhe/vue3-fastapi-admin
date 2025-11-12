from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import RoleBrief, UserRead

router = APIRouter()


@router.get("/", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_db)) -> list[UserRead]:
    repo = UserRepository(db)
    users = await repo.list_users()
    response: list[UserRead] = []
    for user in users:
        response.append(
            UserRead(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                role_ids=[role.id for role in user.roles],
                roles=[RoleBrief(id=role.id, code=role.code, name=role.name) for role in user.roles],
                permissions=sorted(
                    {
                        f"{perm.namespace}:{perm.resource}:{perm.action}"
                        if perm.namespace
                        else f"{perm.resource}:{perm.action}"
                        for role in user.roles
                        for perm in role.permissions
                    }
                ),
            )
        )
    return response

