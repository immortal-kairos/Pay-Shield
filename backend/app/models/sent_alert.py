import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Uuid
from app.models.user import Base

class SentAlert(Base):
    __tablename__ = "sent_alerts"
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(Uuid(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    recipient_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    alert_type = Column(String, nullable=False)
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint('payment_id', 'recipient_user_id', 'alert_type', name='uq_sent_alert'),
    )