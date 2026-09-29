from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID

class PaymentCreate(BaseModel):
    vendor_id: UUID
    amount: float
    currency: str
    payment_date: date
    reference_note: Optional[str] = None

class PaymentResponse(BaseModel):
    id: UUID
    vendor_id: UUID
    vendor_name: Optional[str] = None
    amount: float
    currency: str
    payment_date: date
    status: str
    risk_score: float 
    risk_level: str
    reference_note: Optional[str] = None
    created_at: datetime

    # Additive ML scoring fields
    ml_risk_score: Optional[float] = None
    ml_risk_label: Optional[str] = None
    ml_feature_snapshot: Optional[Dict[str, Any]] = None
    ml_available: bool = False

    class Config:
        from_attributes = True

# --- NEW MODELS ADDED BELOW ---

class PaymentApprove(BaseModel):
    """Payload for approving a single payment"""
    totp_code: Optional[str] = None

class PaymentReject(BaseModel):
    """Payload for rejecting a single payment"""
    rejection_reason: str = Field(
        ..., 
        min_length=5, 
        description="Reason for rejecting the payment (minimum 5 characters)"
    )