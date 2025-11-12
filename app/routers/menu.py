from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.responses import success_response
from app.repositories.menu_repository import MenuRepository
from app.repositories.user_repository import UserRepository
from app.schemas.menu import MenuCreate, MenuUpdate

router = APIRouter()


@router.get("/")
async def list_menus(db: AsyncSession = Depends(get_db)) -> dict:
    menu_repo = MenuRepository(db)
    tree = await menu_repo.fetch_admin_tree()
    return success_response({"list": tree})


@router.get("/routes")
async def get_menu_routes(
    username: str = Query(..., description="Username to load menus for"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user_repo = UserRepository(db)
    user = await user_repo.get_by_username(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    menu_repo = MenuRepository(db)
    routes = await menu_repo.fetch_routes_for_roles(
        [role.id for role in user.roles], include_all=user.is_superuser
    )
    return success_response(routes)


@router.get("/{menu_id}")
async def get_menu_detail(menu_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.get_menu(menu_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    return success_response(menu_repo.serialize_menu(menu))


@router.post("/")
async def create_menu(payload: MenuCreate, db: AsyncSession = Depends(get_db)) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.create_menu(payload)
    return success_response(menu_repo.serialize_menu(menu))


@router.put("/{menu_id}")
async def update_menu(menu_id: int, payload: MenuUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.get_menu(menu_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    menu = await menu_repo.update_menu(menu, payload)
    return success_response(menu_repo.serialize_menu(menu))


@router.delete("/{menu_id}")
async def delete_menu(menu_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    menu_repo = MenuRepository(db)
    menu = await menu_repo.get_menu(menu_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    try:
        await menu_repo.delete_menu(menu)
    except ValueError as exc:
        if str(exc) == "MENU_HAS_CHILDREN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Please remove child menus first"
            ) from exc
        raise
    return success_response({"deleted": True})
