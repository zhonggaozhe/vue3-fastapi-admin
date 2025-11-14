from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.identity import AuthenticatedUser
from app.core.auth import (
    ensure_permission,
    get_current_user,
    permission_required,
)
from app.core.database import get_db
from app.core.responses import success_response
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    RoleBrief,
    UserCreatePayload,
    UserDeletePayload,
    UserRead,
    UserSavePayload,
    UserUpdatePayload,
)

router = APIRouter()


@router.get("/list")
@permission_required("user", "list")
async def list_users(
    db: AsyncSession = Depends(get_db),
) -> dict:
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
    return success_response(response)


@router.post("/save")
async def save_user(
    payload: UserSavePayload,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    repo = UserRepository(db)
    if payload.id:
        await ensure_permission(current_user, "user", "update")
        user = await repo.get_by_id(payload.id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return await _update_user(repo, user, UserUpdatePayload(**payload.model_dump()))
    await ensure_permission(current_user, "user", "create")
    return await _create_user(repo, payload)


@router.post("/edit")
@permission_required("user", "update")
async def edit_user(
    payload: UserUpdatePayload,
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = UserRepository(db)
    user = await repo.get_by_id(payload.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await _update_user(repo, user, payload)


@router.post("/del")
@permission_required("user", "delete")
async def delete_user(
    payload: UserDeletePayload,
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = UserRepository(db)
    deleted = await repo.delete_users(payload.ids)
    return success_response({"deleted": deleted})


async def _create_user(repo: UserRepository, payload: UserCreatePayload) -> dict:
    try:
        user = await repo.create_user(payload)
    except ValueError as exc:
        _handle_user_value_error(exc)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="USER_ALREADY_EXISTS"
        ) from None
    return success_response({"id": user.id})


async def _update_user(
    repo: UserRepository, user, payload: UserUpdatePayload
) -> dict:
    try:
        updated = await repo.update_user(user, payload)
    except ValueError as exc:
        _handle_user_value_error(exc)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="USER_ALREADY_EXISTS"
        ) from None
    return success_response({"id": updated.id})


def _handle_user_value_error(exc: ValueError) -> None:
    message = str(exc)
    if message in {"SUPER_ADMIN_RESERVED", "SUPER_ADMIN_IMMUTABLE"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="USER_INVALID_OPERATION"
    ) from exc
