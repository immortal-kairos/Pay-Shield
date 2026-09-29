import uuid
from fastapi import APIRouter, Depends, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.models.user import UserRole
from app.schemas.export import ExportPaymentsRequest, ExportQueuedResponse
from app.services.export_service import ExportService
from app.core.errors import PayShieldError, ErrorCode

router = APIRouter(prefix="/api/analytics/exports", tags=["exports"])

@router.post("/payments", response_model=ExportQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_export(
    request_body: ExportPaymentsRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.CHECKER]))
):
    if request_body.start_date and request_body.end_date:
        if request_body.start_date > request_body.end_date:
            raise PayShieldError(
                status_code=status.HTTP_400_BAD_REQUEST,
                error=ErrorCode.INVALID_DATE_RANGE,
                message="start_date cannot be after end_date"
            )

    job_id = uuid.uuid4()
    
    background_tasks.add_task(
        ExportService.generate_payments_csv,
        db,
        current_user["org_id"],
        job_id,
        request_body
    )
    
    return ExportQueuedResponse(job_id=job_id, status="queued")


@router.get("/{job_id}/download")
async def download_export(
    job_id: uuid.UUID,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.CHECKER]))
):
    file_path = ExportService.EXPORT_DIR / f"{job_id}.csv"
    
    if not file_path.exists():
        raise PayShieldError(
            status_code=status.HTTP_404_NOT_FOUND,
            error=ErrorCode.EXPORT_FILE_NOT_FOUND,
            message="The requested export file was not found or has expired."
        )
        
    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename=f"payshield_export_{job_id}.csv"
    )