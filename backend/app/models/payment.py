import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Date, ForeignKey, Enum, JSON, Uuid, Text, Boolean
from sqlalchemy.orm import relationship
from app.models.user import Base

class PaymentStatus(str, enum.Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    TRANSFER_INITIATED = "TRANSFER_INITIATED"
    TRANSFER_SUCCESS = "TRANSFER_SUCCESS"
    TRANSFER_FAILED = "TRANSFER_FAILED"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(Uuid(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    vendor_id = Column(Uuid(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    payment_date = Column(Date, nullable=False)
    reference_note = Column(String, nullable=True)

    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING_APPROVAL, nullable=False)
    risk_score = Column(Float, nullable=False, default=0.0)
    risk_flags = Column(JSON, default=list)
    risk_level = Column(String, nullable=False, default="LOW")

    created_by_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reviewed_by_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # US-07 Payment Rail Fields
    provider_reference_id = Column(String, nullable=True)
    transfer_status = Column(String, nullable=True)
    transfer_initiated_at = Column(DateTime(timezone=True), nullable=True)
    transfer_completed_at = Column(DateTime(timezone=True), nullable=True)
    transfer_failure_reason = Column(Text, nullable=True)

    # US-19 ML Fields
    ml_risk_score = Column(Float, nullable=True)
    ml_risk_label = Column(String, nullable=True)
    ml_feature_snapshot = Column(JSON, nullable=True)
    ml_available = Column(Boolean, default=False, nullable=False)

    vendor = relationship("Vendor")