from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:  # pragma: no cover
    from app.models.role import Role, Permission

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
    title_i18n: Mapped[str | None] = mapped_column(String(128), nullable=True)
    path: Mapped[str] = mapped_column(String(255))
    component: Mapped[str | None] = mapped_column(String(255))
    redirect: Mapped[str | None] = mapped_column(String(255))
    order: Mapped[int] = mapped_column(Integer, default=0)
    icon: Mapped[str | None] = mapped_column(String(128))
    type: Mapped[MenuType] = mapped_column(
        SqlEnum(MenuType, values_callable=lambda enum_cls: [e.value for e in enum_cls], name="menu_type"),
        default=MenuType.ROUTE,
    )
    is_external: Mapped[bool] = mapped_column(Boolean, default=False)
    always_show: Mapped[bool] = mapped_column(Boolean, default=False)
    keep_alive: Mapped[bool] = mapped_column(Boolean, default=True)
    affix: Mapped[bool] = mapped_column(Boolean, default=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    active_menu: Mapped[str | None] = mapped_column(String(255))
    show_breadcrumb: Mapped[bool] = mapped_column(Boolean, default=True)
    no_tags_view: Mapped[bool] = mapped_column(Boolean, default=False)
    can_to: Mapped[bool] = mapped_column(Boolean, default=False)

    parent: Mapped["Menu | None"] = relationship(remote_side="Menu.id", backref="children")
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", back_populates="menu", cascade="all, delete-orphan"
    )
    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="role_menus", back_populates="menus", lazy="selectin"
    )
