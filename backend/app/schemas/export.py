from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

class ExportPaymentsRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None

class ExportQueuedResponse(BaseModel):
    job_id: UUID
    status: str = "queued"