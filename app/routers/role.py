from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import permission_required
from app.core.database import get_db
from app.core.responses import success_response
from app.core.settings import get_settings
from app.repositories.menu_repository import MenuRepository
from app.repositories.role_repository import RoleRepository
from app.schemas.role import RoleCreate, RoleDeletePayload, RoleEditPayload, RoleUpdate

router = APIRouter()
legacy_router = APIRouter(prefix="/role")

settings = get_settings()


def _format_datetime(value) -> str | None:
    if not value:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _serialize_role(role, menu_repo: MenuRepository) -> dict:
    menu_tree = menu_repo.build_tree_from_menus(role.menus, include_details=True)
    return {
        "id": role.id,
        "roleName": role.name,
        "role": role.code,
        "status": 1 if role.is_active else 0,
        "createTime": _format_datetime(role.created_at),
        "remark": role.description,
        "menu": menu_tree,
    }


async def _role_list_payload(db: AsyncSession) -> dict:
    role_repo = RoleRepository(db)
    menu_repo = MenuRepository(db)
    roles = await role_repo.list_roles_with_menus()
    role_items = [
        _serialize_role(role, menu_repo)
        for role in roles
        if role.code != settings.super_admin_role_code
    ]
    return success_response({"list": role_items, "total": len(role_items)})


@router.get("/list")
@permission_required("role", "list")
async def list_roles_alias(
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await _role_list_payload(db)


@legacy_router.get("/list")
@permission_required("role", "list")
async def legacy_role_list(
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await _role_list_payload(db)


@router.post("/save")
@permission_required("role", "create")
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    if payload.role_code == settings.super_admin_role_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="SUPER_ADMIN_RESERVED"
        )
    role_repo = RoleRepository(db)
    menu_repo = MenuRepository(db)
    try:
        role = await role_repo.create_role(payload)
    except ValueError as exc:
        message = str(exc)
        if message == "ROLE_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="ROLE_CODE_OR_NAME_EXISTS"
            ) from exc
        if message == "SUPER_ADMIN_RESERVED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="SUPER_ADMIN_RESERVED"
            ) from exc
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="ROLE_CODE_OR_NAME_EXISTS"
        ) from None
    return success_response(_serialize_role(role, menu_repo))


@router.post("/edit")
@permission_required("role", "update")
async def edit_role(payload: RoleEditPayload, db: AsyncSession = Depends(get_db)) -> dict:
    role_repo = RoleRepository(db)
    menu_repo = MenuRepository(db)
    role = await role_repo.get_role(payload.id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    update_payload = RoleUpdate(**payload.model_dump(exclude={"id"}))
    try:
        role = await role_repo.update_role(role, update_payload)
    except ValueError as exc:
        message = str(exc)
        if message == "ROLE_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="ROLE_CODE_OR_NAME_EXISTS"
            ) from exc
        if message == "SUPER_ADMIN_RESERVED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="SUPER_ADMIN_RESERVED"
            ) from exc
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="ROLE_CODE_OR_NAME_EXISTS"
        ) from None
    return success_response(_serialize_role(role, menu_repo))


@router.put("/{role_id}")
@permission_required("role", "update")
async def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    role_repo = RoleRepository(db)
    menu_repo = MenuRepository(db)
    role = await role_repo.get_role(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.code == settings.super_admin_role_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="SUPER_ADMIN_IMMUTABLE"
        )
    try:
        role = await role_repo.update_role(role, payload)
    except ValueError as exc:
        message = str(exc)
        if message == "ROLE_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="ROLE_CODE_OR_NAME_EXISTS"
            ) from exc
        if message == "SUPER_ADMIN_RESERVED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="SUPER_ADMIN_RESERVED"
            ) from exc
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="ROLE_CODE_OR_NAME_EXISTS"
        ) from None
    return success_response(_serialize_role(role, menu_repo))


@router.post("/del")
@permission_required("role", "delete")
async def delete_roles(payload: RoleDeletePayload, db: AsyncSession = Depends(get_db)) -> dict:
    role_repo = RoleRepository(db)
    deleted = 0
    for role_id in payload.ids:
        role = await role_repo.get_role(role_id)
        if not role:
            continue
        try:
            await role_repo.delete_role(role)
        except ValueError as exc:
            message = str(exc)
            if message == "ROLE_IN_USE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="ROLE_IN_USE"
                ) from exc
            if message == "SUPER_ADMIN_IMMUTABLE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="SUPER_ADMIN_IMMUTABLE"
                ) from exc
            raise
        else:
            deleted += 1
    return success_response({"deleted": deleted})


@router.delete("/{role_id}")
@permission_required("role", "delete")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    role_repo = RoleRepository(db)
    role = await role_repo.get_role(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.code == settings.super_admin_role_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="SUPER_ADMIN_IMMUTABLE"
        )
    try:
        await role_repo.delete_role(role)
    except ValueError as exc:
        message = str(exc)
        if message == "ROLE_IN_USE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="ROLE_IN_USE"
            ) from exc
        if message == "SUPER_ADMIN_IMMUTABLE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="SUPER_ADMIN_IMMUTABLE"
            ) from exc
        raise
    return success_response({"deleted": True})
