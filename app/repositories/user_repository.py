from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.security import hash_password
from app.models.role import Permission, Role
from app.models.user import User
from app.schemas.user import UserCreatePayload


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_username(self, username: str) -> User | None:
        stmt = (
            select(User)
            .where(User.username == username)
            .options(joinedload(User.roles).joinedload(Role.permissions))
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().first()

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(joinedload(User.roles).joinedload(Role.permissions))
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().first()

    async def list_users(self) -> Sequence[User]:
        stmt = (
            select(User)
            .options(
                joinedload(User.roles).joinedload(Role.permissions),
                selectinload(User.department),
            )
            .order_by(User.id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def list_by_department(
        self, department_id: int | None, page_index: int, page_size: int
    ) -> tuple[list[User], int]:
        stmt = (
            select(User)
            .options(
                joinedload(User.roles).joinedload(Role.permissions),
                selectinload(User.department),
            )
            .order_by(User.id)
        )
        count_stmt = select(func.count()).select_from(User)
        if department_id:
            stmt = stmt.where(User.department_id == department_id)
            count_stmt = count_stmt.where(User.department_id == department_id)

        total = await self.session.scalar(count_stmt) or 0
        offset = (page_index - 1) * page_size
        result = await self.session.execute(stmt.offset(offset).limit(page_size))
        users = result.scalars().unique().all()
        return users, total

    async def create_user(self, payload: UserCreatePayload) -> User:
        user = User(
            username=payload.account,
            email=payload.email,
            full_name=payload.username,
            password_hash=hash_password(payload.password or payload.account or "123456"),
            is_active=True,
            roles=[],
        )
        if payload.department and payload.department.id not in (None, "", 0):
            user.department_id = int(payload.department.id)
        self.session.add(user)
        if payload.role:
            result = await self.session.execute(select(Role).where(Role.id.in_(payload.role)))
            roles = result.scalars().unique().all()
            user.roles.extend(roles)
        await self.session.commit()
        return await self.get_by_id(user.id)
