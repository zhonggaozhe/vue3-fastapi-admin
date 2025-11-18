from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.audit import AuditAgent, get_audit_agent
from app.agents.identity import AuthenticatedUser
from app.core.audit_actions import AuditAction
from app.core.auth import (
    ensure_permission,
    get_current_user,
    permission_guard,
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


@router.get("/list", dependencies=[permission_guard("user", "list")])
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


@router.post("/save", dependencies=[permission_guard("user", "create")])
async def save_user(
    payload: UserSavePayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
    audit_agent: AuditAgent = Depends(get_audit_agent),
) -> dict:
    repo = UserRepository(db)
    if payload.id:
        await ensure_permission(current_user, "user", "update")
        user = await repo.get_by_id(payload.id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return await _update_user(
            repo,
            user,
            UserUpdatePayload(**payload.model_dump()),
            request=request,
            operator=current_user,
            audit_agent=audit_agent,
        )
    await ensure_permission(current_user, "user", "create")
    return await _create_user(
        repo,
        payload,
        request=request,
        operator=current_user,
        audit_agent=audit_agent,
    )


@router.post("/edit", dependencies=[permission_guard("user", "update")])
async def edit_user(
    payload: UserUpdatePayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
    audit_agent: AuditAgent = Depends(get_audit_agent),
) -> dict:
    repo = UserRepository(db)
    user = await repo.get_by_id(payload.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await _update_user(
        repo,
        user,
        payload,
        request=request,
        operator=current_user,
        audit_agent=audit_agent,
    )


@router.post("/del", dependencies=[permission_guard("user", "delete")])
async def delete_user(
    payload: UserDeletePayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
    audit_agent: AuditAgent = Depends(get_audit_agent),
) -> dict:
    repo = UserRepository(db)
    deleted = await repo.delete_users(payload.ids)
    if deleted:
        await audit_agent.log_event(
            action=AuditAction.USER_DELETE,
            resource_type="USER",
            resource_id=",".join(str(_id) for _id in payload.ids),
            operator_id=current_user.id,
            operator_name=current_user.username,
            params={"ids": payload.ids},
            request=request,
        )
    return success_response({"deleted": deleted})


async def _create_user(
    repo: UserRepository,
    payload: UserCreatePayload,
    *,
    request: Request,
    operator: AuthenticatedUser,
    audit_agent: AuditAgent,
) -> dict:
    try:
        user = await repo.create_user(payload)
    except ValueError as exc:
        _handle_user_value_error(exc)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="USER_ALREADY_EXISTS"
        ) from None
    snapshot = _user_snapshot(user)
    await audit_agent.log_event(
        action=AuditAction.ADMIN_CREATE_USER,
        resource_type="USER",
        resource_id=str(user.id),
        operator_id=operator.id,
        operator_name=operator.username,
        after_state=snapshot,
        params=payload.model_dump(exclude={"password"}),
        request=request,
    )
    return success_response({"id": user.id})


async def _update_user(
    repo: UserRepository,
    user,
    payload: UserUpdatePayload,
    *,
    request: Request,
    operator: AuthenticatedUser,
    audit_agent: AuditAgent,
) -> dict:
    try:
        before_snapshot = _user_snapshot(user)
        updated = await repo.update_user(user, payload)
    except ValueError as exc:
        _handle_user_value_error(exc)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="USER_ALREADY_EXISTS"
        ) from None
    after_snapshot = _user_snapshot(updated)
    await audit_agent.log_event(
        action=AuditAction.USER_PROFILE_UPDATE,
        resource_type="USER",
        resource_id=str(updated.id),
        operator_id=operator.id,
        operator_name=operator.username,
        before_state=before_snapshot,
        after_state=after_snapshot,
        params=payload.model_dump(exclude={"password"}),
        request=request,
    )
    if payload.password:
        await audit_agent.log_event(
            action=AuditAction.USER_PASSWORD_UPDATE,
            resource_type="USER",
            resource_id=str(updated.id),
            operator_id=operator.id,
            operator_name=operator.username,
            before_state={"password_updated": False},
            after_state={"password_updated": True},
            params={"initiator": operator.username},
            request=request,
        )
    return success_response({"id": updated.id})


def _handle_user_value_error(exc: ValueError) -> None:
    message = str(exc)
    if message in {"SUPER_ADMIN_RESERVED", "SUPER_ADMIN_IMMUTABLE"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="USER_INVALID_OPERATION"
    ) from exc


def _user_snapshot(user) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "department_id": user.department_id,
        "role_ids": sorted(role.id for role in user.roles),
        "role_codes": sorted(role.code for role in user.roles),
    }
