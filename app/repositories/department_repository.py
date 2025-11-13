from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department


class DepartmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def fetch_tree(self) -> list[dict[str, Any]]:
        result = await self.session.execute(select(Department))
        departments = result.scalars().unique().all()
        return self._build_tree(departments)

    async def fetch_tree_with_pagination(
        self, page_index: int, page_size: int
    ) -> tuple[list[dict[str, Any]], int]:
        tree = await self.fetch_tree()
        total = len(tree)
        start = (page_index - 1) * page_size
        end = start + page_size
        return tree[start:end], total

    def _build_tree(self, departments: list[Department]) -> list[dict[str, Any]]:
        if not departments:
            return []

        children_map: dict[int | None, list[Department]] = defaultdict(list)
        for dept in departments:
            children_map[dept.parent_id].append(dept)

        for dept_list in children_map.values():
            dept_list.sort(key=lambda d: (d.order, d.id))

        def serialize(dept: Department) -> dict[str, Any]:
            node = {
                "id": str(dept.id),
                "departmentName": dept.name,
                "status": 1 if dept.is_active else 0,
                "remark": dept.remark,
                "createTime": self._format_datetime(dept.created_at),
            }
            children = [serialize(child) for child in children_map.get(dept.id, [])]
            if children:
                node["children"] = children
            return node

        return [serialize(dept) for dept in children_map.get(None, [])]

    @staticmethod
    def _format_datetime(value) -> str | None:
        if not value:
            return None
        return value.strftime("%Y-%m-%d %H:%M:%S")
