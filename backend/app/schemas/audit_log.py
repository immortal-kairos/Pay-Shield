from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Any, Optional

class AuditLogEntry(BaseModel):
    id: UUID
    org_id: UUID
    event_type: str
    entity_type: str
    entity_id: UUID
    actor_user_id: UUID
    metadata_: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class AuditLogPaginatedResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[AuditLogEntry]
    