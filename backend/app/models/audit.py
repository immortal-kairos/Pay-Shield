import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Uuid
from sqlalchemy import event
from app.models.user import Base

class AuditEventType(str, enum.Enum):
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    VENDOR_CREATED = "VENDOR_CREATED"
    VENDOR_APPROVED = "VENDOR_APPROVED"
    VENDOR_REJECTED = "VENDOR_REJECTED"
    PAYMENT_CREATED = "PAYMENT_CREATED"
    PAYMENT_APPROVED = "PAYMENT_APPROVED"
    PAYMENT_REJECTED = "PAYMENT_REJECTED"
    TOTP_SETUP_INITIATED = "TOTP_SETUP_INITIATED"
    TOTP_SETUP_COMPLETE = "TOTP_SETUP_COMPLETE"
    TOTP_BACKUP_CODE_USED = "TOTP_BACKUP_CODE_USED"
    TOTP_APPROVAL_SUCCESS = "TOTP_APPROVAL_SUCCESS"
    TOTP_APPROVAL_FAILED = "TOTP_APPROVAL_FAILED"
    EMAIL_ALERT_SENT = "EMAIL_ALERT_SENT"
    EMAIL_ALERT_FAILED = "EMAIL_ALERT_FAILED"
    # US-07 Events
    PAYMENT_TRANSFER_INITIATED = "PAYMENT_TRANSFER_INITIATED"
    PAYMENT_TRANSFER_SUCCESS = "PAYMENT_TRANSFER_SUCCESS"
    PAYMENT_TRANSFER_FAILED = "PAYMENT_TRANSFER_FAILED"

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(Uuid(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    event_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Uuid(as_uuid=True), nullable=False)
    actor_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

@event.listens_for(AuditLog, 'before_update')
def receive_before_update(mapper, connection, target):
    raise NotImplementedError("Audit log entries are immutable and cannot be updated.")

@event.listens_for(AuditLog, 'before_delete')
def receive_before_delete(mapper, connection, target):
    raise NotImplementedError("Audit log entries are append-only and cannot be deleted.")