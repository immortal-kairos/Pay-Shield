from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from app.core.dependencies import get_db, require_role
from app.models.user import User, UserRole
from app.models.totp_backup_code import TOTPBackupCode
from app.models.audit_log import AuditEventType
from app.services.audit_log_service import AuditLogService
from app.services.totp_service import TOTPService
from app.core import encryption
from app.core.security import get_password_hash, verify_password
from app.core.errors import PayShieldError, ErrorCode
from app.schemas.totp import TOTPVerify, TOTPBackup

router = APIRouter(prefix="/api/auth/totp", tags=["totp"])

@router.get("/setup")
async def setup_totp(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.CHECKER]))
):
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalars().first()

    if user.totp_enabled:
        raise PayShieldError(400, ErrorCode.TOTP_REQUIRED, "2FA is already configured on this account.")

    secret = TOTPService.generate_secret()
    user.totp_secret_encrypted = encryption.encrypt(secret)
    
    backup_codes = TOTPService.generate_backup_codes()
    for code in backup_codes:
        bc = TOTPBackupCode(
            user_id=user.id,
            code_hash=get_password_hash(code),
            used=False
        )
        db.add(bc)
    
    await AuditLogService.write(db, current_user["org_id"], AuditEventType.TOTP_SETUP_INITIATED, "user", user.id, user.id)
    await db.commit()

    return {
        "totp_uri": TOTPService.generate_totp_uri(secret, user.email),
        "backup_codes": backup_codes,
        "message": "Scan the QR code with your authenticator app, then call /verify to activate."
    }

@router.post("/verify")
async def verify_totp(
    payload: TOTPVerify,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.CHECKER]))
):
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalars().first()

    if not user.totp_secret_encrypted:
        raise PayShieldError(400, ErrorCode.TOTP_REQUIRED, "TOTP setup has not been initiated. Call /setup first.")

    plain_secret = encryption.decrypt(user.totp_secret_encrypted)
    if not TOTPService.verify_code(plain_secret, payload.totp_code):
        raise PayShieldError(401, ErrorCode.TOTP_INVALID, "Invalid or expired 2FA code.")

    user.totp_enabled = True
    user.totp_verified_at = datetime.now(timezone.utc)

    await AuditLogService.write(db, current_user["org_id"], AuditEventType.TOTP_SETUP_COMPLETE, "user", user.id, user.id)
    await db.commit()

    return {"totp_enabled": True, "message": "2FA successfully activated."}

@router.post("/backup")
async def use_backup_code(
    payload: TOTPBackup,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.CHECKER]))
):
    result = await db.execute(select(TOTPBackupCode).where(TOTPBackupCode.user_id == current_user["id"], TOTPBackupCode.used == False))
    backup_codes = result.scalars().all()

    for bc in backup_codes:
        if verify_password(payload.backup_code, bc.code_hash):
            bc.used = True
            bc.used_at = datetime.now(timezone.utc)
            remaining = len(backup_codes) - 1
            await AuditLogService.write(db, current_user["org_id"], AuditEventType.TOTP_BACKUP_CODE_USED, "user", current_user["id"], current_user["id"], {"codes_remaining": remaining})
            await db.commit()
            return {"verified": True, "codes_remaining": remaining}
    
    raise PayShieldError(401, ErrorCode.TOTP_INVALID, "Invalid or already used backup code.")
    