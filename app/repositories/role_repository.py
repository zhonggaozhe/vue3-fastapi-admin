from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.menu import Menu
from app.models.role import Role
from app.models.user import UserRole
from app.schemas.role import RoleCreate, RoleUpdate


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _base_query(self):
        return select(Role).options(
            selectinload(Role.menus).selectinload(Menu.actions),
            selectinload(Role.permissions),
            selectinload(Role.users),
        )

    async def list_roles_with_menus(self) -> Sequence[Role]:
        stmt = self._base_query().order_by(Role.id)
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_role(self, role_id: int) -> Role | None:
        stmt = self._base_query().where(Role.id == role_id)
        result = await self.session.execute(stmt)
        return result.scalars().unique().first()

    async def create_role(self, payload: RoleCreate) -> Role:
        await self._ensure_unique(code=payload.role_code, name=payload.role_name)
        role = Role(
            code=payload.role_code,
            name=payload.role_name,
            description=payload.remark,
            is_active=bool(payload.status),
            menus=[],
        )
        self.session.add(role)
        await self.session.flush()
        await self._assign_menus(role, payload.menu_ids, replace=True)
        await self.session.commit()
        return await self.get_role(role.id)

    async def update_role(self, role: Role, payload: RoleUpdate) -> Role:
        await self._ensure_unique(code=payload.role_code, name=payload.role_name, exclude_id=role.id)
        role.code = payload.role_code
        role.name = payload.role_name
        role.description = payload.remark
        role.is_active = bool(payload.status)
        await self._assign_menus(role, payload.menu_ids, replace=True)
        await self.session.commit()
        return await self.get_role(role.id)

    async def delete_role(self, role: Role) -> None:
        user_count = await self.session.scalar(
            select(func.count()).select_from(UserRole).where(UserRole.role_id == role.id)
        )
        if user_count and user_count > 0:
            raise ValueError("ROLE_IN_USE")
        await self.session.delete(role)
        await self.session.commit()

    async def _assign_menus(self, role: Role, menu_ids: list[int], replace: bool = False) -> None:
        if replace:
            role.menus = []
        if menu_ids:
            result = await self.session.execute(
                select(Menu)
                .where(Menu.id.in_(menu_ids))
                .options(selectinload(Menu.actions))
            )
            menus = result.scalars().unique().all()
            role.menus.extend(menus)

    async def _ensure_unique(self, *, code: str, name: str, exclude_id: int | None = None) -> None:
        stmt = select(Role.id).where(or_(Role.code == code, Role.name == name))
        if exclude_id is not None:
            stmt = stmt.where(Role.id != exclude_id)
        exists = await self.session.scalar(stmt.limit(1))
        if exists:
            raise ValueError("ROLE_EXISTS")
