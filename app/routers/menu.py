from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.identity import AuthenticatedUser
from app.core.auth import permission_required, require_authenticated_user
from app.core.database import get_db
from app.core.errors import raise_error
from app.core.responses import success_response
from app.repositories.menu_repository import MenuRepository
from app.repositories.user_repository import UserRepository
from app.schemas.menu import MenuCreate, MenuDeletePayload, MenuEditPayload, MenuUpdate

router = APIRouter()

async def _menu_list_payload(db: AsyncSession) -> dict:
    menu_repo = MenuRepository(db)
    tree = await menu_repo.fetch_admin_tree()
    return success_response({"list": tree})


@router.get("/list")
@permission_required("menu", "list")
async def list_menus_alias(
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await _menu_list_payload(db)


@router.get("/routes")
async def get_menu_routes(
    username: str | None = Query(None, description="Deprecated. Username is derived from token."),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    user_repo = UserRepository(db)
    token_username = current_user.username
    lookup_username = username or token_username
    if lookup_username != token_username and not current_user.is_superuser:
        raise_error("AUTH.FORBIDDEN")
    user = await user_repo.get_by_username(lookup_username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    menu_repo = MenuRepository(db)
    routes = await menu_repo.fetch_routes_for_roles(
        [role.id for role in user.roles], include_all=user.is_superuser
    )
    return success_response(routes)


@router.get("/{menu_id}")
@permission_required("menu", "list")
async def get_menu_detail(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.get_menu(menu_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    return success_response(menu_repo.serialize_menu(menu))


@router.post("/save")
@permission_required("menu", "create")
async def create_menu(
    payload: MenuCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.create_menu(payload)
    return success_response(menu_repo.serialize_menu(menu))


@router.post("/edit")
@permission_required("menu", "update")
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


@router.put("/{menu_id}")
@permission_required("menu", "update")
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


@router.post("/del")
@permission_required("menu", "delete")
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


@router.delete("/{menu_id}")
@permission_required("menu", "delete")
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
