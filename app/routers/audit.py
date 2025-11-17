from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.identity import AuthenticatedUser
from app.core.auth import get_current_user, permission_guard
from app.core.database import get_db
from app.core.responses import success_response
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogListResponse, AuditLogQuery, AuditLogRead

router = APIRouter()


@router.get("/list", response_model=dict, dependencies=[permission_guard("audit", "list")])
async def list_audit_logs(
    operator_id: int | None = Query(default=None),
    operator_name: str | None = Query(default=None),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    resource_id: str | None = Query(default=None),
    result_status: int | None = Query(default=None),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """查询审计日志列表"""
    conditions = []
    
    if operator_id is not None:
        conditions.append(AuditLog.operator_id == operator_id)
    if operator_name:
        conditions.append(AuditLog.operator_name.ilike(f"%{operator_name}%"))
    if action:
        conditions.append(AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if resource_id:
        conditions.append(AuditLog.resource_id == resource_id)
    if result_status is not None:
        conditions.append(AuditLog.result_status == result_status)
    if start_time:
        conditions.append(AuditLog.created_at >= start_time)
    if end_time:
        conditions.append(AuditLog.created_at <= end_time)
    
    # 计算总数
    count_stmt = select(func.count(AuditLog.id))
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    result = await db.execute(count_stmt)
    total = result.scalar() or 0
    
    # 查询数据
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return success_response({
        "list": [AuditLogRead.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get(
    "/{log_id}",
    response_model=dict,
    dependencies=[permission_guard("audit", "read")],
)
async def get_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """获取单个审计日志详情"""
    stmt = select(AuditLog).where(AuditLog.id == log_id)
    result = await db.execute(stmt)
    log = result.scalar_one_or_none()
    
    if not log:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
    
    return success_response(AuditLogRead.model_validate(log))
