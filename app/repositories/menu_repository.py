from __future__ import annotations

from collections import defaultdict
from typing import Any, Literal

from sqlalchemy import Select, delete, select, union_all
from sqlalchemy.orm import aliased, selectinload

from app.models.menu import Menu, MenuType
from app.models.role import Permission, RoleMenu, RolePermission
from app.core.logging import get_logger

logger = get_logger(__name__)

class MenuRepository:
    def __init__(self, session):
        self.session = session

    def _base_query(self) -> Select[tuple[Menu]]:
        return select(Menu).options(selectinload(Menu.permissions), selectinload(Menu.parent))

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
        action_code_map = None
        if not include_all:
            action_code_map = await self._get_role_action_map(role_ids)
        return self._build_route_tree(menus, mode="route", action_code_map=action_code_map)

    async def fetch_admin_tree(self) -> list[dict[str, Any]]:
        result = await self.session.execute(self._base_query())
        menus = result.scalars().unique().all()
        return self._build_route_tree(menus, mode="compact")

    def build_tree_from_menus(
        self,
        menus: list[Menu],
        include_details: bool = True,
        action_code_map: dict[int, set[str]] | None = None,
        action_id_map: dict[int, set[int]] | None = None,
    ) -> list[dict[str, Any]]:
        mode: Literal["full", "route"] = "full" if include_details else "route"
        return self._build_route_tree(
            menus,
            mode=mode,
            action_code_map=action_code_map,
            action_id_map=action_id_map,
        )

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

    async def add_action(self, menu: Menu, label: str, value: str) -> Permission:
        namespace, resource, action_value = self._parse_permission_value(value)
        permission = Permission(
            menu=menu,
            label=label,
            namespace=namespace,
            resource=resource,
            action=action_value,
            effect="allow",
        )
        self.session.add(permission)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(permission)
        return permission

    async def update_action(self, menu: Menu, action_id: int, label: str, value: str) -> Permission:
        action = next((item for item in menu.permissions if item.id == action_id), None)
        if not action:
            raise ValueError("ACTION_NOT_FOUND")
        namespace, resource, action_value = self._parse_permission_value(value)
        action.label = label
        action.namespace = namespace
        action.resource = resource
        action.action = action_value
        await self.session.commit()
        await self.session.refresh(action)
        return action

    async def delete_action(self, menu: Menu, action_id: int) -> None:
        action = next((item for item in menu.permissions if item.id == action_id), None)
        if not action:
            raise ValueError("ACTION_NOT_FOUND")
        await self.session.delete(action)
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

    def _parse_permission_value(self, raw: str) -> tuple[str, str, str]:
        if not raw:
            raise ValueError("INVALID_PERMISSION_VALUE")
        parts = [part.strip() for part in raw.split(":") if part.strip()]
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        if len(parts) == 2:
            return "system", parts[0], parts[1]
        raise ValueError("INVALID_PERMISSION_VALUE")

    @staticmethod
    def _permission_code(permission: Permission) -> str:
        namespace = (permission.namespace or "").strip()
        resource = permission.resource.strip()
        action = permission.action.strip()
        if namespace == resource == action == "*":
            return "*.*.*"
        if namespace:
            return f"{namespace}:{resource}:{action}"
        return f"{resource}:{action}"

    @staticmethod
    def _permission_code_from_parts(namespace: str | None, resource: str, action: str) -> str:
        namespace = (namespace or "").strip()
        resource = resource.strip()
        action = action.strip()
        if namespace == resource == action == "*":
            return "*.*.*"
        if namespace:
            return f"{namespace}:{resource}:{action}"
        return f"{resource}:{action}"

    def _sync_actions(self, menu: Menu, permissions: list) -> None:
        existing = {perm.id: perm for perm in menu.permissions}
        next_permissions: list[Permission] = []
        for item in permissions or []:
            value = getattr(item, "value", None)
            label = getattr(item, "label", None)
            if not value:
                continue
            namespace, resource, action = self._parse_permission_value(value)
            perm_id = getattr(item, "id", None)
            if perm_id and perm_id in existing:
                permission = existing.pop(perm_id)
                permission.namespace = namespace
                permission.resource = resource
                permission.action = action
                permission.label = label
                permission.menu = menu
                next_permissions.append(permission)
            else:
                next_permissions.append(
                    Permission(
                        namespace=namespace,
                        resource=resource,
                        action=action,
                        label=label,
                        menu=menu,
                        effect="allow",
                    )
                )
        for permission in existing.values():
            self.session.delete(permission)
        menu.permissions = next_permissions

    def serialize_menu(self, menu: Menu) -> dict[str, Any]:
        parent_title = menu.parent.title if menu.parent else None
        return self._menu_dict(menu, parent_title=parent_title)

    def _menu_dict(self, menu: Menu, parent_title: str | None = None) -> dict[str, Any]:
        permission_codes = [self._permission_code(permission) for permission in menu.permissions]
        permission_ids = [permission.id for permission in menu.permissions]
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
            "permission": permission_codes,
            "permissionIds": permission_ids,
        }
        permission_list = [
            {"id": permission.id, "label": permission.label, "value": self._permission_code(permission)}
            for permission in menu.permissions
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

    async def _get_role_action_map(
        self, role_ids: list[int]
    ) -> dict[int, set[str]] | None:
        if not role_ids:
            return None
        stmt = (
            select(
                RolePermission.role_id,
                Permission.menu_id,
                Permission.namespace,
                Permission.resource,
                Permission.action,
            )
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id.in_(role_ids))
            .where(Permission.menu_id.is_not(None))
        )
        result = await self.session.execute(stmt)
        action_map: dict[int, set[str]] = defaultdict(set)
        for _, menu_id, namespace, resource, action in result:
            if menu_id is None:
                continue
            code = self._permission_code_from_parts(namespace, resource, action)
            action_map[int(menu_id)].add(code)
        return action_map or None

    def _build_route_tree(
        self,
        menus: list[Menu],
        mode: Literal["full", "route", "compact"],
        action_code_map: dict[int, set[str]] | None = None,
        action_id_map: dict[int, set[int]] | None = None,
    ) -> list[dict[str, Any]]:
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
            title_value = (
                menu.title if mode in ("full", "compact") else menu.title_i18n or menu.title
            )
            allowed_codes: set[str] | None = None
            allowed_ids: set[int] | None = None
            if action_code_map is not None:
                allowed_codes = action_code_map.get(menu.id)
            if action_id_map is not None:
                allowed_ids = action_id_map.get(menu.id)
            permission_entries = [
                (permission, self._permission_code(permission)) for permission in menu.permissions
            ]
            if allowed_codes is None:
                permission_codes = [code for _, code in permission_entries]
            else:
                permission_codes = [code for _, code in permission_entries if code in allowed_codes]
            if allowed_ids is None:
                permission_ids = [
                    permission.id for permission, _ in permission_entries if permission.id is not None
                ]
            else:
                permission_ids = [
                    permission.id
                    for permission, _ in permission_entries
                    if permission.id in allowed_ids
                ]
            permission_list = [
                {"id": permission.id, "label": permission.label, "value": code}
                for permission, code in permission_entries
            ]
            meta = {
                "title": title_value,
                "icon": menu.icon,
                "hidden": menu.hidden,
                "alwaysShow": menu.always_show,
                "noCache": not menu.keep_alive,
                "breadcrumb": menu.show_breadcrumb,
                "affix": menu.affix,
                "noTagsView": menu.no_tags_view,
                "activeMenu": menu.active_menu,
                "canTo": menu.can_to,
                "permission": permission_codes,
                "permissionIds": permission_ids,
            }
            if mode == "full":
                meta["titleKey"] = menu.title_i18n or menu.title

            children = [build(child) for child in children_map.get(menu.id, [])]

            if mode == "full":
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
                node["children"] = children
                return node

            if mode == "compact":
                node = {
                    "path": menu.path,
                    "component": menu.component or "#",
                    "redirect": menu.redirect,
                    "name": menu.name,
                    "meta": meta,
                    "id": menu.id,
                    "parentId": menu.parent_id,
                    "title": menu.title,
                    "status": 1 if menu.enabled else 0,
                    "type": 0 if menu.type == MenuType.DIRECTORY else 1,
                    "permissionList": permission_list,
                }
                node["children"] = children
                return node

            route_node = {
                "path": menu.path,
                "component": menu.component or "#",
                "redirect": menu.redirect,
                "name": menu.name,
                "meta": meta,
            }
            route_node["children"] = children
            return route_node

        roots = children_map.get(None, [])
        return [build(menu) for menu in roots]
