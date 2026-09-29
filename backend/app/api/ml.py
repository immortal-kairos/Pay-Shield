from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.dependencies.auth import require_admin_role
from backend.app.schemas.ml import MLHealthResponse, MLTrainResponse
from backend.app.ml.model_service import model_service
from backend.app.ml.train_isolation_forest import execute_training_pipeline

router = APIRouter(prefix="/api/ml", tags=["ML Anomaly Engine"])

@router.get("/health", response_model=MLHealthResponse)
def get_ml_health(current_user: Any = Depends(require_admin_role)):
    meta = model_service.get_metadata()
    trained_at_str = meta.get("trained_at")

    trained_at_dt = None
    if trained_at_str:
        try:
            trained_at_dt = datetime.fromisoformat(trained_at_str)
        except ValueError:
            trained_at_dt = None

    return MLHealthResponse(
        model_ready=model_service.is_model_ready(),
        artifact_path=model_service.get_artifact_path(),
        feature_count=meta.get("feature_count", 15),
        trained_at=trained_at_dt
    )

@router.post("/train", response_model=MLTrainResponse)
def trigger_training(
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_admin_role)
):
    try:
        summary = execute_training_pipeline(db)
        # Hot-reload in-memory model
        model_service.load_model()

        return MLTrainResponse(
            rows_used=summary["rows_used"],
            feature_count=summary["feature_count"],
            artifact_written=True,
            trained_at=datetime.fromisoformat(summary["trained_at"])
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training encountered an unexpected error: {str(e)}"
        )