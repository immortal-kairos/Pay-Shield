import json
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Header, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.dependencies import get_db
from app.core.config import settings
from app.services.payment_rail_service import PaymentRailService
from app.services.audit_log_service import AuditLogService
from app.models.payment import Payment
from app.models.audit_log import AuditLog, AuditEventType

router = APIRouter(prefix="/api/webhooks/razorpay", tags=["webhooks"])

@router.post("")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if not x_razorpay_signature:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Missing signature"})

    raw_body = await request.body()
    
    is_valid = PaymentRailService.verify_webhook_signature(
        raw_body, 
        x_razorpay_signature, 
        settings.RAZORPAY_WEBHOOK_SECRET
    )

    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Invalid signature"})

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Invalid JSON"})

    event_type = payload.get("event")
    
    if event_type not in ["payout.processed", "payout.failed"]:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ignored"})

    try:
        payout_data = payload["payload"]["payout"]["entity"]
        payout_id = payout_data["id"]
    except KeyError:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "malformed_payload"})

    payment_result = await db.execute(select(Payment).where(Payment.provider_reference_id == payout_id))
    payment = payment_result.scalars().first()

    if not payment:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "payment_not_found"})

    # Idempotency Check
    existing_audit_result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_id == payment.id,
            AuditLog.event_type.in_([AuditEventType.PAYMENT_TRANSFER_SUCCESS.value, AuditEventType.PAYMENT_TRANSFER_FAILED.value])
        )
    )
    if existing_audit_result.scalars().first():
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "already_processed"})

    utc_now = datetime.now(timezone.utc)
    
    # Fallback to the Maker's ID if the Checker's ID is missing to satisfy the NOT NULL constraint
    actor_id = payment.reviewed_by_user_id or payment.created_by_user_id

    if event_type == "payout.processed":
        payment.transfer_status = 'SUCCESS'
        payment.transfer_completed_at = utc_now
        await AuditLogService.write(db, payment.org_id, AuditEventType.PAYMENT_TRANSFER_SUCCESS, "payment", payment.id, actor_id)

    elif event_type == "payout.failed":
        failure_reason = payout_data.get("failure_reason", "Unknown failure")
        payment.transfer_status = 'FAILED'
        payment.transfer_failure_reason = failure_reason
        await AuditLogService.write(db, payment.org_id, AuditEventType.PAYMENT_TRANSFER_FAILED, "payment", payment.id, actor_id, {"reason": failure_reason})

    await db.commit()
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "processed"})