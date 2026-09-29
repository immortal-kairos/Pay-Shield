from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db, require_role
from app.models.user import UserRole
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentApprove, PaymentReject
from app.services import payment_service
from app.schemas.bulk import BulkPaymentActionRequest, BulkRejectPaymentRequest, BulkActionResponse
from app.services import bulk_action_service

router = APIRouter(prefix="/api/payments", tags=["payments"])

# ---------------------------------------------------------------------------
# 1. BULK ACTION ROUTES (Defined FIRST to prevent path capture)
# ---------------------------------------------------------------------------

@router.post("/bulk-approve", response_model=BulkActionResponse)
async def bulk_approve_payments_route(
    request: BulkPaymentActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.CHECKER, UserRole.ADMIN]))
):
    return await bulk_action_service.bulk_approve_payments(
        db=db,
        org_id=str(current_user["org_id"]),
        payment_ids=request.payment_ids,
        actor_user_id=str(current_user["id"])
    )


@router.post("/bulk-reject", response_model=BulkActionResponse)
async def bulk_reject_payments_route(
    request: BulkRejectPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.CHECKER, UserRole.ADMIN]))
):
    return await bulk_action_service.bulk_reject_payments(
        db=db,
        org_id=str(current_user["org_id"]),
        payment_ids=request.payment_ids,
        reason=request.rejection_reason,
        actor_user_id=str(current_user["id"])
    )


# ---------------------------------------------------------------------------
# 2. STANDARD COLLECTION ROUTES
# ---------------------------------------------------------------------------

@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_in: PaymentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.MAKER]))
):
    return await payment_service.create_payment(db, payment_in, current_user, background_tasks)


@router.get("", response_model=List[PaymentResponse])
async def list_payments(
    status_filter: Optional[PaymentStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.MAKER, UserRole.CHECKER, UserRole.ADMIN]))
):
    # THE FIX: Cast the string ID back to a UUID object so SQLAlchemy doesn't crash!
    org_uuid = UUID(current_user["org_id"])
    
    query = select(Payment).where(Payment.org_id == org_uuid)
    
    if status_filter:
        query = query.where(Payment.status == status_filter)
        
    result = await db.execute(query.options(selectinload(Payment.vendor)))
    payments = result.scalars().all()
    
    # Map the vendor_name attribute to satisfy the Pydantic schema
    for p in payments:
        p.vendor_name = p.vendor.name if p.vendor else "Unknown Vendor"
        
    return payments


# ---------------------------------------------------------------------------
# 3. DYNAMIC PARAMETER ROUTES
# ---------------------------------------------------------------------------

@router.post("/{payment_id}/approve", response_model=PaymentResponse)
async def approve_payment(
    payment_id: UUID,
    payload: PaymentApprove,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.CHECKER]))
):
    return await payment_service.approve_payment(
        db=db, 
        payment_id=payment_id, 
        current_user=current_user, 
        background_tasks=background_tasks,
        totp_code=payload.totp_code
    )


@router.post("/{payment_id}/reject", response_model=PaymentResponse)
async def reject_payment(
    payment_id: UUID,
    payload: PaymentReject,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.CHECKER]))
):
    return await payment_service.reject_payment(
        db=db, 
        payment_id=payment_id, 
        reason=payload.rejection_reason, 
        current_user=current_user,
        background_tasks=background_tasks
    )