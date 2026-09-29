import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Uuid
from sqlalchemy.orm import relationship
from app.models.user import Base

class VendorStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(Uuid(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    name = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)
    bank_account_hash = Column(String, nullable=False)
    bank_account_last4 = Column(String(4), nullable=False)
    bank_account_encrypted = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=False)
    tax_id = Column(String, nullable=True)
    status = Column(Enum(VendorStatus), default=VendorStatus.PENDING_REVIEW, nullable=False)
    created_by_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    bank_account_updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))