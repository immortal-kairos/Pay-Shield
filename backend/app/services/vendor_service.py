from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.vendor import Vendor, VendorStatus
from app.models.audit_log import AuditEventType
from app.schemas.vendor import VendorCreate
from app.core.security import get_password_hash
from app.services.audit_log_service import AuditLogService
from app.core.errors import PayShieldError, ErrorCode

async def create_vendor(db: AsyncSession, vendor_in: VendorCreate, current_user: dict) -> Vendor:
    hashed_account = get_password_hash(vendor_in.bank_account_number)
    last4 = vendor_in.bank_account_number[-4:]

    new_vendor = Vendor(
        org_id=current_user["org_id"],
        name=vendor_in.name,
        contact_email=vendor_in.contact_email,
        bank_account_hash=hashed_account,
        bank_account_last4=last4,
        ifsc_code=vendor_in.ifsc_code,
        tax_id=vendor_in.tax_id,
        created_by_user_id=current_user["id"]
    )
    db.add(new_vendor)
    await db.flush()

    await AuditLogService.write(db, current_user["org_id"], AuditEventType.VENDOR_CREATED, "vendor", new_vendor.id, current_user["id"])
    await db.commit()
    await db.refresh(new_vendor)
    return new_vendor

async def approve_vendor(db: AsyncSession, vendor_id: UUID, current_user: dict) -> Vendor:
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id, Vendor.org_id == current_user["org_id"]))
    vendor = result.scalars().first()
    
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    if str(vendor.created_by_user_id) == str(current_user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot approve a vendor you created")
    if vendor.status == VendorStatus.ACTIVE:
        raise PayShieldError(400, ErrorCode.INACTIVE_VENDOR, "Vendor is already active")

    vendor.status = VendorStatus.ACTIVE
    vendor.approved_by_user_id = current_user["id"]
    
    await AuditLogService.write(db, current_user["org_id"], AuditEventType.VENDOR_APPROVED, "vendor", vendor.id, current_user["id"])
    await db.commit()
    await db.refresh(vendor)
    return vendor

async def reject_vendor(db: AsyncSession, vendor_id: UUID, reason: str, current_user: dict) -> Vendor:
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id, Vendor.org_id == current_user["org_id"]))
    vendor = result.scalars().first()
    
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    
    vendor.status = VendorStatus.REJECTED
    vendor.rejection_reason = reason
    vendor.approved_by_user_id = current_user["id"]
    
    await AuditLogService.write(db, current_user["org_id"], AuditEventType.VENDOR_REJECTED, "vendor", vendor.id, current_user["id"], {"reason": reason})
    await db.commit()
    await db.refresh(vendor)
    return vendor

async def prevent_active_vendor_edits(db: AsyncSession, vendor_id: UUID):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalars().first()
    if vendor and vendor.status == VendorStatus.ACTIVE:
        raise PayShieldError(
            status_code=400,
            error=ErrorCode.BANK_DETAILS_IMMUTABLE,
            message="Bank details cannot be edited on an active vendor. Create a new vendor record."
        )