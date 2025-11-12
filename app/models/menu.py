from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:  # pragma: no cover
    from app.models.role import Role


class MenuType(str, Enum):
    DIRECTORY = "directory"
    ROUTE = "route"
    ACTION = "action"


class Menu(TimestampMixin, Base):
    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("menus.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(128), unique=True)
    title: Mapped[str] = mapped_column(String(128))
    path: Mapped[str] = mapped_column(String(255))
    component: Mapped[str | None] = mapped_column(String(255))
    redirect: Mapped[str | None] = mapped_column(String(255))
    order: Mapped[int] = mapped_column(Integer, default=0)
    icon: Mapped[str | None] = mapped_column(String(128))
    type: Mapped[MenuType] = mapped_column(SqlEnum(MenuType), default=MenuType.ROUTE)
    is_external: Mapped[bool] = mapped_column(Boolean, default=False)
    always_show: Mapped[bool] = mapped_column(Boolean, default=False)
    keep_alive: Mapped[bool] = mapped_column(Boolean, default=True)
    affix: Mapped[bool] = mapped_column(Boolean, default=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    parent: Mapped["Menu | None"] = relationship(remote_side="Menu.id", backref="children")
    actions: Mapped[list["MenuAction"]] = relationship(
        "MenuAction", back_populates="menu", cascade="all,delete-orphan"
    )
    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="role_menus", back_populates="menus", lazy="selectin"
    )


class MenuAction(TimestampMixin, Base):
    __tablename__ = "menu_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(String(255))

    menu: Mapped["Menu"] = relationship("Menu", back_populates="actions")

