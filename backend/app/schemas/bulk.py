from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional

class BulkItemResult(BaseModel):
    id: UUID
    status: str            # "APPROVED" | "REJECTED" | "FAILED"
    error: Optional[str] = None

class BulkActionResponse(BaseModel):
    results: List[BulkItemResult]
    approved_count: int = 0
    rejected_count: int = 0
    failed_count: int = 0

class BulkPaymentActionRequest(BaseModel):
    payment_ids: List[UUID] = Field(..., min_length=1, max_length=50)

class BulkRejectPaymentRequest(BaseModel):
    payment_ids: List[UUID] = Field(..., min_length=1, max_length=50)
    rejection_reason: str = Field(..., min_length=5, max_length=500)

class BulkVendorActionRequest(BaseModel):
    vendor_ids: List[UUID] = Field(..., min_length=1, max_length=50)

class BulkRejectVendorRequest(BaseModel):
    vendor_ids: List[UUID] = Field(..., min_length=1, max_length=50)
    rejection_reason: str = Field(..., min_length=5, max_length=500)