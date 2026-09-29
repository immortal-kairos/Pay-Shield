from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class MLHealthResponse(BaseModel):
    model_ready: bool
    artifact_path: str
    feature_count: int
    trained_at: Optional[datetime] = None

class MLTrainResponse(BaseModel):
    rows_used: int
    feature_count: int
    artifact_written: bool
    trained_at: datetime

class MLResultExtension(BaseModel):
    ml_risk_score: Optional[float] = Field(None, description="Normalized anomaly risk score between 0 and 100")
    ml_risk_label: Optional[str] = Field(None, description="LOW, MEDIUM, or HIGH")
    ml_feature_snapshot: Optional[Dict[str, Any]] = Field(None, description="Deterministic snapshot of engineered features")
    ml_available: bool = False