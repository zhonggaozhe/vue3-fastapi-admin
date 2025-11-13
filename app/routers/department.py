from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.responses import success_response
from app.repositories.department_repository import DepartmentRepository
from app.repositories.user_repository import UserRepository

router = APIRouter()
legacy_router = APIRouter(prefix="/department")


def _format_datetime(value) -> str | None:
    if not value:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")


async def _department_tree_payload(db: AsyncSession) -> dict:
    repo = DepartmentRepository(db)
    data = await repo.fetch_tree()
    return success_response({"list": data})


@router.get("/list")
async def list_departments(db: AsyncSession = Depends(get_db)) -> dict:
    return await _department_tree_payload(db)


@legacy_router.get("/list")
async def legacy_list_departments(db: AsyncSession = Depends(get_db)) -> dict:
    return await _department_tree_payload(db)


async def _department_table_payload(
    page_index: int, page_size: int, db: AsyncSession
) -> dict:
    repo = DepartmentRepository(db)
    data, total = await repo.fetch_tree_with_pagination(page_index, page_size)
    return success_response({"list": data, "total": total})


@router.get("/table/list")
async def department_table_list(
    pageIndex: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await _department_table_payload(pageIndex, pageSize, db)


@legacy_router.get("/table/list")
async def legacy_department_table_list(
    pageIndex: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await _department_table_payload(pageIndex, pageSize, db)


async def _department_users_payload(
    dept_id: str | None, page_index: int, page_size: int, db: AsyncSession
) -> dict:
    repo = UserRepository(db)
    department_id = int(dept_id) if dept_id not in (None, "", "0") else None
    users, total = await repo.list_by_department(department_id, page_index, page_size)

    def serialize(user):
        dept = user.department
        department_info = (
            {"id": str(dept.id), "departmentName": dept.name} if dept else None
        )
        role_names = [role.name for role in user.roles]
        return {
            "id": str(user.id),
            "username": user.full_name or user.username,
            "account": user.username,
            "email": user.email,
            "createTime": _format_datetime(user.created_at),
            "role": ", ".join(role_names),
            "department": department_info,
        }

    return success_response({"list": [serialize(user) for user in users], "total": total})


@router.get("/users")
async def department_users(
    id: str | None = Query(default=None, description="Department ID"),
    pageIndex: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await _department_users_payload(id, pageIndex, pageSize, db)


@legacy_router.get("/users")
async def legacy_department_users(
    id: str | None = Query(default=None, description="Department ID"),
    pageIndex: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await _department_users_payload(id, pageIndex, pageSize, db)
