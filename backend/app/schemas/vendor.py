from pydantic import BaseModel, EmailStr, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.vendor import VendorStatus

class VendorCreate(BaseModel):
    name: str
    contact_email: EmailStr
    bank_account_number: str = Field(..., min_length=8)
    ifsc_code: str
    tax_id: Optional[str] = None

class VendorReject(BaseModel):
    rejection_reason: str = Field(..., min_length=5)

class VendorResponse(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    contact_email: EmailStr
    bank_account_last4: str
    ifsc_code: str
    tax_id: Optional[str]
    status: VendorStatus
    bank_account_updated_at: datetime
    created_by_user_id: UUID
    approved_by_user_id: Optional[UUID]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)