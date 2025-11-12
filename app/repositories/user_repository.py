from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.role import Permission, Role
from app.models.user import User


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
            .options(joinedload(User.roles).joinedload(Role.permissions))
            .order_by(User.id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()
