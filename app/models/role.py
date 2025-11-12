from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.types import jsonb

if TYPE_CHECKING:  # pragma: no cover
    from app.models.user import User
    from app.models.menu import Menu


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    users: Mapped[list["User"]] = relationship(
        "User", secondary="user_roles", back_populates="roles", lazy="selectin"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary="role_permissions", lazy="selectin", back_populates="roles"
    )
    menus: Mapped[list["Menu"]] = relationship(
        "Menu", secondary="role_menus", lazy="selectin", back_populates="roles"
    )


class Permission(TimestampMixin, Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    namespace: Mapped[str] = mapped_column(String(128), index=True)
    resource: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64))
    label: Mapped[str | None] = mapped_column(String(128))
    effect: Mapped[str] = mapped_column(String(16), default="allow")
    condition: Mapped[dict | None] = mapped_column(jsonb)

    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="role_permissions", lazy="selectin", back_populates="permissions"
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"))
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"))


class RoleMenu(Base):
    __tablename__ = "role_menus"
    __table_args__ = (UniqueConstraint("role_id", "menu_id", name="uq_role_menu"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"))
    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.id", ondelete="CASCADE"))
