from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class ReportScheduleCreateRequest(BaseModel):
    name: str
    export_type: str
    frequency: str
    recipient_emails: List[str]
    filters: Optional[Dict[str, Any]] = None

class ReportScheduleResponse(BaseModel):
    id: UUID
    name: str
    export_type: str
    frequency: str
    recipient_emails: List[str]
    filters: Optional[Dict[str, Any]]
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True