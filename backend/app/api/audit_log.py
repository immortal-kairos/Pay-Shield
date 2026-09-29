from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc

from app.schemas.audit_log import AuditLogPaginatedResponse
from app.models.audit_log import AuditLog
from app.models.user import UserRole
from app.core.dependencies import get_db, require_role

router = APIRouter(prefix="/api/audit-log", tags=["audit-log"])

@router.get("", response_model=AuditLogPaginatedResponse)
async def read_audit_log(
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    query = select(AuditLog).where(AuditLog.org_id == current_user["org_id"])

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
    if from_date:
        query = query.where(AuditLog.created_at >= from_date)
    if to_date:
        query = query.where(AuditLog.created_at <= to_date)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate and fetch
    query = query.order_by(desc(AuditLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": items
    }