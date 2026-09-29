from pydantic import BaseModel
from typing import Dict, List

class TopVendor(BaseModel):
    vendor_name: str
    total_volume: float

class DashboardMetrics(BaseModel):
    total_volume_inr: float
    payment_count_by_status: Dict[str, int]
    high_risk_payments_count: int
    top_vendors_by_volume: List[TopVendor]