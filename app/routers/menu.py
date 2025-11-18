from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.identity import AuthenticatedUser
from app.agents.rbac import RBACAgent
from app.core.auth import permission_guard, require_authenticated_user
from app.core.database import get_db
from app.core.errors import raise_error
from app.core.responses import success_response
from app.repositories.menu_repository import MenuRepository
from app.schemas.menu import (
    MenuCreate,
    MenuDeletePayload,
    MenuEditPayload,
    MenuPermissionPayload,
    MenuUpdate,
)

router = APIRouter()
_rbac_agent = RBACAgent()

async def _menu_list_payload(db: AsyncSession) -> dict:
    menu_repo = MenuRepository(db)
    tree = await menu_repo.fetch_admin_tree()
    return success_response({"list": tree})


@router.get("/list", dependencies=[permission_guard("menu", "list")])
async def list_menus_alias(
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await _menu_list_payload(db)


@router.get("/routes")
async def get_menu_routes(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    menu_repo = MenuRepository(db)
    routes = await menu_repo.fetch_routes_for_roles(
        [role.id for role in current_user.roles], include_all=current_user.is_superuser
    )
    principal = await _rbac_agent.build_principal(current_user)
    return success_response({"routes": routes, "user": principal})


@router.get("/{menu_id}", dependencies=[permission_guard("menu", "list")])
async def get_menu_detail(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.get_menu(menu_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    return success_response(menu_repo.serialize_menu(menu))


@router.post("/save", dependencies=[permission_guard("menu", "create")])
async def create_menu(
    payload: MenuCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.create_menu(payload)
    return success_response(menu_repo.serialize_menu(menu))


@router.post("/edit", dependencies=[permission_guard("menu", "update")])
async def edit_menu(
    payload: MenuEditPayload,
    db: AsyncSession = Depends(get_db),
) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.get_menu(payload.id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    update_payload = MenuUpdate(**payload.model_dump(exclude={"id"}))
    menu = await menu_repo.update_menu(menu, update_payload)
    return success_response(menu_repo.serialize_menu(menu))


@router.put("/{menu_id}", dependencies=[permission_guard("menu", "update")])
async def update_menu(
    menu_id: int,
    payload: MenuUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.get_menu(menu_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    menu = await menu_repo.update_menu(menu, payload)
    return success_response(menu_repo.serialize_menu(menu))


@router.post("/del", dependencies=[permission_guard("menu", "delete")])
async def delete_menu_batch(
    payload: MenuDeletePayload,
    db: AsyncSession = Depends(get_db),
) -> dict:
    menu_repo = MenuRepository(db)
    deleted = 0
    for menu_id in payload.ids:
        menu = await menu_repo.get_menu(menu_id)
        if not menu:
            continue
        try:
            await menu_repo.delete_menu(menu, force=payload.force)
        except ValueError as exc:
            if str(exc) == "MENU_HAS_CHILDREN":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Please remove child menus first"
                ) from exc
            raise
        else:
            deleted += 1
    return success_response({"deleted": deleted})


@router.delete("/{menu_id}", dependencies=[permission_guard("menu", "delete")])
async def delete_menu(
    menu_id: int,
    force: bool = Query(False, description="是否级联删除子菜单"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.get_menu(menu_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    try:
        await menu_repo.delete_menu(menu, force=force)
    except ValueError as exc:
        if str(exc) == "MENU_HAS_CHILDREN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Please remove child menus first"
            ) from exc
        raise
    return success_response({"deleted": True})


@router.post(
    "/{menu_id}/actions",
    dependencies=[permission_guard("menu", "update")],
)
async def create_menu_action(
    menu_id: int,
    payload: MenuPermissionPayload,
    db: AsyncSession = Depends(get_db),
) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.get_menu(menu_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    try:
        namespace, resource, action_value = menu_repo._parse_permission_value(payload.value)
    except ValueError as exc:  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_PERMISSION_VALUE") from exc
    normalized_value = menu_repo._permission_code_from_parts(namespace, resource, action_value)
    if any(
        menu_repo._permission_code(action) == normalized_value for action in menu.permissions
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ACTION_EXISTS")
    action = await menu_repo.add_action(menu, payload.label, payload.value)
    return success_response(
        {"id": action.id, "label": action.label, "value": menu_repo._permission_code(action)}
    )


@router.put(
    "/{menu_id}/actions/{action_id}",
    dependencies=[permission_guard("menu", "update")],
)
async def update_menu_action(
    menu_id: int,
    action_id: int,
    payload: MenuPermissionPayload,
    db: AsyncSession = Depends(get_db),
) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.get_menu(menu_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    try:
        try:
            namespace, resource, action_value = menu_repo._parse_permission_value(payload.value)
        except ValueError as exc:  # type: ignore[attr-defined]
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_PERMISSION_VALUE") from exc
        normalized_value = menu_repo._permission_code_from_parts(namespace, resource, action_value)
        if any(
            menu_repo._permission_code(action) == normalized_value and action.id != action_id
            for action in menu.permissions
        ):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ACTION_EXISTS")
        action = await menu_repo.update_action(menu, action_id, payload.label, payload.value)
    except ValueError as exc:
        if str(exc) == "ACTION_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found") from exc
        raise
    return success_response(
        {"id": action.id, "label": action.label, "value": menu_repo._permission_code(action)}
    )


@router.delete(
    "/{menu_id}/actions/{action_id}",
    dependencies=[permission_guard("menu", "update")],
)
async def delete_menu_action(
    menu_id: int,
    action_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.get_menu(menu_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    try:
        await menu_repo.delete_action(menu, action_id)
    except ValueError as exc:
        if str(exc) == "ACTION_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found") from exc
        raise
    return success_response({"deleted": True})
