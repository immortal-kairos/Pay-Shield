import uuid
from datetime import datetime, timezone

# 1. FIXED: Using 'Uuid' instead of 'UUID'
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Uuid

# 2. FIXED: Using your project's exact Base location
from app.models.user import Base 

class ReportSchedule(Base):
    __tablename__ = "report_schedules"
    
    # Notice we are using Uuid(as_uuid=True) here
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(Uuid(as_uuid=True), nullable=False)
    created_by_user_id = Column(Uuid(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    export_type = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    recipient_emails = Column(JSON, nullable=False)
    filters = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)