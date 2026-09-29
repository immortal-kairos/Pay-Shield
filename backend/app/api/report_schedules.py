import uuid
from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.models.user import UserRole
from app.schemas.report_schedule import ReportScheduleCreateRequest, ReportScheduleResponse
from app.services.report_schedule_service import ReportScheduleService

router = APIRouter(prefix="/api/analytics/report-schedules", tags=["report_schedules"])

@router.post("", response_model=ReportScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    payload: ReportScheduleCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    return await ReportScheduleService.create_schedule(db, current_user["org_id"], current_user["id"], payload)

@router.get("", response_model=List[ReportScheduleResponse])
async def list_schedules(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    return await ReportScheduleService.list_schedules(db, current_user["org_id"])

@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    return await ReportScheduleService.delete_schedule(db, current_user["org_id"], schedule_id)

@router.post("/run-due")
async def run_due(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    base_url = str(request.base_url).rstrip('/')
    return await ReportScheduleService.run_due_schedules(db, base_url)