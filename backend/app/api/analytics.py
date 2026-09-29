from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.models.user import UserRole
from app.schemas.analytics import DashboardMetrics
from app.services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.CHECKER]))
):
    return await analytics_service.get_dashboard_metrics(
        db=db, 
        org_id=current_user["org_id"], 
        start_date=start_date, 
        end_date=end_date
    )