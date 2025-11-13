from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import Select, delete, select, union_all
from sqlalchemy.orm import aliased, selectinload

from app.models.menu import Menu, MenuAction, MenuType
from app.models.role import RoleMenu


class MenuRepository:
    def __init__(self, session):
        self.session = session

    def _base_query(self) -> Select[tuple[Menu]]:
        return select(Menu).options(selectinload(Menu.actions), selectinload(Menu.parent))

    async def fetch_routes_for_roles(
        self, role_ids: list[int], include_all: bool
    ) -> list[dict[str, Any]]:
        stmt = self._base_query().where(Menu.enabled.is_(True))
        if not include_all:
            if not role_ids:
                return []
            stmt = stmt.join(RoleMenu, RoleMenu.menu_id == Menu.id).filter(
                RoleMenu.role_id.in_(role_ids)
            )
        result = await self.session.execute(stmt)
        menus = result.scalars().unique().all()
        return self._build_route_tree(menus, include_details=False)

    async def fetch_admin_tree(self) -> list[dict[str, Any]]:
        result = await self.session.execute(self._base_query())
        menus = result.scalars().unique().all()
        return self._build_route_tree(menus, include_details=True)

    def build_tree_from_menus(
        self, menus: list[Menu], include_details: bool = True
    ) -> list[dict[str, Any]]:
        return self._build_route_tree(menus, include_details=include_details)

    async def get_menu(self, menu_id: int) -> Menu | None:
        result = await self.session.execute(
            self._base_query().where(Menu.id == menu_id)
        )
        return result.scalar_one_or_none()

    async def create_menu(self, payload) -> Menu:
        menu = Menu()
        self._assign_fields(menu, payload)
        self.session.add(menu)
        await self.session.flush()
        self._sync_actions(menu, payload.permission_list)
        await self.session.commit()
        await self.session.refresh(menu)
        return menu

    async def update_menu(self, menu: Menu, payload) -> Menu:
        self._assign_fields(menu, payload)
        self._sync_actions(menu, payload.permission_list)
        await self.session.commit()
        await self.session.refresh(menu)
        return menu

    async def delete_menu(self, menu: Menu, force: bool = False) -> None:
        if force:
            await self._delete_subtree(menu.id)
            return

        child_exists = await self.session.scalar(
            select(Menu.id).where(Menu.parent_id == menu.id).limit(1)
        )
        if child_exists:
            raise ValueError("MENU_HAS_CHILDREN")
        await self.session.delete(menu)
        await self.session.commit()

    async def _delete_subtree(self, root_id: int) -> None:
        menu_cte = select(Menu.id).where(Menu.id == root_id).cte(name="menu_tree", recursive=True)
        menu_alias = aliased(Menu)
        menu_cte = menu_cte.union_all(
            select(menu_alias.id).where(menu_alias.parent_id == menu_cte.c.id)
        )
        stmt = select(menu_cte.c.id)
        result = await self.session.execute(stmt)
        ids = [row[0] for row in result]
        if not ids:
            return
        await self.session.execute(delete(Menu).where(Menu.id.in_(ids)))
        await self.session.commit()

    def _assign_fields(self, menu: Menu, payload) -> None:
        meta = payload.meta
        parent_id = payload.parent_id if payload.parent_id not in (0, "") else None
        menu.parent_id = parent_id
        menu.name = payload.name
        menu.title = meta.title
        menu.title_i18n = meta.title_key or meta.title
        menu.component = payload.component
        menu.path = payload.path
        menu.redirect = payload.redirect or None
        menu.icon = meta.icon
        menu.order = getattr(payload, "order", None) or menu.order or 0
        menu.type = MenuType.DIRECTORY if payload.type == 0 else MenuType.ROUTE
        menu.is_external = str(menu.path).startswith("http")
        menu.always_show = bool(meta.always_show)
        menu.keep_alive = not bool(meta.no_cache)
        menu.affix = bool(meta.affix)
        menu.hidden = bool(meta.hidden)
        menu.enabled = bool(payload.status)
        menu.active_menu = meta.active_menu or None
        menu.show_breadcrumb = meta.breadcrumb
        menu.no_tags_view = bool(meta.no_tags_view)
        menu.can_to = bool(meta.can_to)

    def _sync_actions(self, menu: Menu, permissions: list) -> None:
        existing = {action.id: action for action in menu.actions}
        next_actions: list[MenuAction] = []
        for item in permissions or []:
            perm_id = getattr(item, "id", None)
            if perm_id and perm_id in existing:
                action = existing.pop(perm_id)
                action.code = item.value
                action.label = item.label
                next_actions.append(action)
            else:
                next_actions.append(
                    MenuAction(code=item.value, label=item.label, menu=menu)
                )
        for action in existing.values():
            self.session.delete(action)
        menu.actions = next_actions

    def serialize_menu(self, menu: Menu) -> dict[str, Any]:
        parent_title = menu.parent.title if menu.parent else None
        return self._menu_dict(menu, parent_title=parent_title)

    def _menu_dict(self, menu: Menu, parent_title: str | None = None) -> dict[str, Any]:
        meta = {
            "title": menu.title,
            "titleKey": menu.title_i18n or menu.title,
            "icon": menu.icon,
            "alwaysShow": menu.always_show,
            "noCache": not menu.keep_alive,
            "breadcrumb": menu.show_breadcrumb,
            "affix": menu.affix,
            "noTagsView": menu.no_tags_view,
            "canTo": menu.can_to,
            "activeMenu": menu.active_menu,
            "hidden": menu.hidden,
            "permission": [action.code for action in menu.actions],
        }
        permission_list = [
            {"id": action.id, "label": action.label, "value": action.code}
            for action in menu.actions
        ]
        data = {
            "id": menu.id,
            "parentId": menu.parent_id,
            "parentName": parent_title,
            "title": menu.title,
            "path": menu.path,
            "name": menu.name,
            "component": menu.component or "#",
            "redirect": menu.redirect,
            "order": menu.order,
            "status": 1 if menu.enabled else 0,
            "type": 0 if menu.type == MenuType.DIRECTORY else 1,
            "meta": meta,
            "permissionList": permission_list,
            "menuState": menu.enabled,
            "enableHidden": menu.hidden,
            "enableDisplay": menu.always_show,
            "enableCleanCache": not menu.keep_alive,
            "enableShowCrumb": menu.show_breadcrumb,
            "enablePinnedTab": menu.affix,
            "enableHiddenTab": menu.no_tags_view,
            "enableSkip": menu.can_to,
        }
        return data

    def _build_route_tree(self, menus: list[Menu], include_details: bool) -> list[dict[str, Any]]:
        if not menus:
            return []

        node_map = {menu.id: menu for menu in menus if menu.type != MenuType.ACTION}
        title_map = {menu.id: menu.title for menu in menus}
        children_map: dict[int | None, list[Menu]] = defaultdict(list)

        for menu in node_map.values():
            children_map[menu.parent_id].append(menu)

        for menu_list in children_map.values():
            menu_list.sort(key=lambda m: (m.order, m.id))

        def build(menu: Menu) -> dict[str, Any]:
            title_value = menu.title if include_details else menu.title_i18n or menu.title
            meta = {
                "title": title_value,
                "titleKey": menu.title_i18n or menu.title,
                "icon": menu.icon,
                "alwaysShow": menu.always_show,
                "noCache": not menu.keep_alive,
                "breadcrumb": menu.show_breadcrumb,
                "affix": menu.affix,
                "noTagsView": menu.no_tags_view,
                "canTo": menu.can_to,
                "activeMenu": menu.active_menu,
                "hidden": menu.hidden,
                "permission": [action.code for action in menu.actions],
            }
            children = [build(child) for child in children_map.get(menu.id, [])]

            if include_details:
                node = {
                    "id": menu.id,
                    "parentId": menu.parent_id,
                    "parentName": title_map.get(menu.parent_id),
                    "title": menu.title,
                    "path": menu.path,
                    "name": menu.name,
                    "component": menu.component or "#",
                    "redirect": menu.redirect,
                    "meta": meta,
                    "status": 1 if menu.enabled else 0,
                    "type": 0 if menu.type == MenuType.DIRECTORY else 1,
                    "permissionList": [
                        {"id": action.id, "label": action.label, "value": action.code}
                        for action in menu.actions
                    ],
                    "menuState": menu.enabled,
                    "enableHidden": menu.hidden,
                    "enableDisplay": menu.always_show,
                    "enableCleanCache": not menu.keep_alive,
                    "enableShowCrumb": menu.show_breadcrumb,
                    "enablePinnedTab": menu.affix,
                    "enableHiddenTab": menu.no_tags_view,
                    "enableSkip": menu.can_to,
                }
                if children:
                    node["children"] = children
                return node

            route_node = {
                "path": menu.path,
                "component": menu.component or "#",
                "redirect": menu.redirect,
                "name": menu.name,
                "meta": meta,
            }
            if children:
                route_node["children"] = children
            return route_node

        roots = children_map.get(None, [])
        return [build(menu) for menu in roots]
