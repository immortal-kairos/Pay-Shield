import logging
from uuid import UUID
from datetime import datetime, timezone
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.payment import Payment
from app.models.vendor import Vendor
from app.schemas.bulk import BulkActionResponse, BulkItemResult
from app.services import payment_service, vendor_service, audit_log_service

logger = logging.getLogger(__name__)

async def bulk_approve_payments(
    db: AsyncSession, payment_ids: list[UUID], current_user: dict
) -> BulkActionResponse:
    results = []
    approved_count, failed_count = 0, 0
    batch_size = len(payment_ids)
    bg_tasks = BackgroundTasks()
    
    org_id = str(current_user["org_id"])
    actor_user_id = str(current_user["id"])

    for payment_id in payment_ids:
        try:
            query = select(Payment).where(Payment.id == payment_id, Payment.org_id == UUID(org_id))
            res = await db.execute(query)
            payment = res.scalars().first()

            if not payment:
                results.append(BulkItemResult(id=payment_id, status="FAILED", error="NOT_FOUND"))
                failed_count += 1
                continue

            status_str = payment.status.value if hasattr(payment.status, 'value') else str(payment.status)
            if status_str != "PENDING_APPROVAL":
                results.append(BulkItemResult(id=payment_id, status="FAILED", error="INVALID_STATE"))
                failed_count += 1
                continue

            await payment_service.approve_payment(
                db=db, payment_id=payment_id, current_user=current_user, background_tasks=bg_tasks, totp_code=None 
            )

            results.append(BulkItemResult(id=payment_id, status="APPROVED"))
            approved_count += 1

            await audit_log_service.log_action(
                db=db, action="BULK_PAYMENT_APPROVED", actor_user_id=actor_user_id, entity_id=str(payment_id),
                details={"batch_size": batch_size, "timestamp": datetime.now(timezone.utc).isoformat()}
            )
        except Exception as e:
            logger.error(f"CRITICAL ERROR on Payment {payment_id}: {str(e)}", exc_info=True)
            results.append(BulkItemResult(id=payment_id, status="FAILED", error=str(e)))
            failed_count += 1

    await db.commit()
    return BulkActionResponse(results=results, approved_count=approved_count, rejected_count=0, failed_count=failed_count)


async def bulk_reject_payments(
    db: AsyncSession, payment_ids: list[UUID], reason: str, current_user: dict
) -> BulkActionResponse:
    results = []
    rejected_count, failed_count = 0, 0
    batch_size = len(payment_ids)
    bg_tasks = BackgroundTasks()
    
    org_id = str(current_user["org_id"])
    actor_user_id = str(current_user["id"])

    for payment_id in payment_ids:
        try:
            query = select(Payment).where(Payment.id == payment_id, Payment.org_id == UUID(org_id))
            res = await db.execute(query)
            payment = res.scalars().first()

            if not payment:
                results.append(BulkItemResult(id=payment_id, status="FAILED", error="NOT_FOUND"))
                failed_count += 1
                continue

            status_str = payment.status.value if hasattr(payment.status, 'value') else str(payment.status)
            if status_str != "PENDING_APPROVAL":
                results.append(BulkItemResult(id=payment_id, status="FAILED", error="INVALID_STATE"))
                failed_count += 1
                continue

            await payment_service.reject_payment(
                db=db, payment_id=payment_id, reason=reason, current_user=current_user, background_tasks=bg_tasks
            )

            results.append(BulkItemResult(id=payment_id, status="REJECTED"))
            rejected_count += 1

            await audit_log_service.log_action(
                db=db, action="BULK_PAYMENT_REJECTED", actor_user_id=actor_user_id, entity_id=str(payment_id),
                details={"batch_size": batch_size, "timestamp": datetime.now(timezone.utc).isoformat()}
            )
        except Exception as e:
            logger.error(f"CRITICAL ERROR on Payment {payment_id}: {str(e)}", exc_info=True)
            results.append(BulkItemResult(id=payment_id, status="FAILED", error=str(e)))
            failed_count += 1

    await db.commit()
    return BulkActionResponse(results=results, approved_count=0, rejected_count=rejected_count, failed_count=failed_count)


async def bulk_approve_vendors(
    db: AsyncSession, vendor_ids: list[UUID], current_user: dict
) -> BulkActionResponse:
    results = []
    approved_count, failed_count = 0, 0
    batch_size = len(vendor_ids)
    bg_tasks = BackgroundTasks()
    
    org_id = str(current_user["org_id"])
    actor_user_id = str(current_user["id"])

    for vendor_id in vendor_ids:
        try:
            query = select(Vendor).where(Vendor.id == vendor_id, Vendor.org_id == UUID(org_id))
            res = await db.execute(query)
            vendor = res.scalars().first()

            if not vendor:
                results.append(BulkItemResult(id=vendor_id, status="FAILED", error="NOT_FOUND"))
                failed_count += 1
                continue

            status_str = vendor.status.value if hasattr(vendor.status, 'value') else str(vendor.status)
            if status_str != "PENDING_APPROVAL" and status_str != "PENDING_REVIEW":
                results.append(BulkItemResult(id=vendor_id, status="FAILED", error="INVALID_STATE"))
                failed_count += 1
                continue

            await vendor_service.approve_vendor(
                db=db, vendor_id=vendor_id, current_user=current_user, background_tasks=bg_tasks
            )

            results.append(BulkItemResult(id=vendor_id, status="APPROVED"))
            approved_count += 1

            await audit_log_service.log_action(
                db=db, action="BULK_VENDOR_APPROVED", actor_user_id=actor_user_id, entity_id=str(vendor_id),
                details={"batch_size": batch_size, "timestamp": datetime.now(timezone.utc).isoformat()}
            )
        except Exception as e:
            logger.error(f"CRITICAL ERROR on Vendor {vendor_id}: {str(e)}", exc_info=True)
            results.append(BulkItemResult(id=vendor_id, status="FAILED", error=str(e)))
            failed_count += 1

    await db.commit()
    return BulkActionResponse(results=results, approved_count=approved_count, rejected_count=0, failed_count=failed_count)


async def bulk_reject_vendors(
    db: AsyncSession, vendor_ids: list[UUID], reason: str, current_user: dict
) -> BulkActionResponse:
    results = []
    rejected_count, failed_count = 0, 0
    batch_size = len(vendor_ids)
    bg_tasks = BackgroundTasks()
    
    org_id = str(current_user["org_id"])
    actor_user_id = str(current_user["id"])

    for vendor_id in vendor_ids:
        try:
            query = select(Vendor).where(Vendor.id == vendor_id, Vendor.org_id == UUID(org_id))
            res = await db.execute(query)
            vendor = res.scalars().first()

            if not vendor:
                results.append(BulkItemResult(id=vendor_id, status="FAILED", error="NOT_FOUND"))
                failed_count += 1
                continue

            status_str = vendor.status.value if hasattr(vendor.status, 'value') else str(vendor.status)
            if status_str != "PENDING_APPROVAL" and status_str != "PENDING_REVIEW":
                results.append(BulkItemResult(id=vendor_id, status="FAILED", error="INVALID_STATE"))
                failed_count += 1
                continue

            await vendor_service.reject_vendor(
                db=db, vendor_id=vendor_id, reason=reason, current_user=current_user, background_tasks=bg_tasks
            )

            results.append(BulkItemResult(id=vendor_id, status="REJECTED"))
            rejected_count += 1

            await audit_log_service.log_action(
                db=db, action="BULK_VENDOR_REJECTED", actor_user_id=actor_user_id, entity_id=str(vendor_id),
                details={"batch_size": batch_size, "timestamp": datetime.now(timezone.utc).isoformat()}
            )
        except Exception as e:
            logger.error(f"CRITICAL ERROR on Vendor {vendor_id}: {str(e)}", exc_info=True)
            results.append(BulkItemResult(id=vendor_id, status="FAILED", error=str(e)))
            failed_count += 1

    await db.commit()
    return BulkActionResponse(results=results, approved_count=0, rejected_count=rejected_count, failed_count=failed_count)