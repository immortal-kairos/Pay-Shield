import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
import joblib
from sklearn.ensemble import IsolationForest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.payment import Payment
from app.ml.feature_builder import build_payment_feature_vector, FEATURE_ORDER
from app.ml.model_service import MODEL_PATH, METADATA_PATH, ARTIFACT_DIR

logger = logging.getLogger("payshield.ml")

MIN_TRAINING_SAMPLES = 10

async def execute_training_pipeline(db: AsyncSession) -> Dict[str, Any]:
    logger.info("ML_TRAINING_STARTED: Extracting historical payments.")

    stmt = select(Payment).order_by(Payment.created_at.asc())
    result = await db.execute(stmt)
    payments = result.scalars().all()

    if len(payments) < MIN_TRAINING_SAMPLES:
        msg = f"Insufficient training data. Minimum {MIN_TRAINING_SAMPLES} samples required; found {len(payments)}."
        logger.error("ML_TRAINING_FAILED: %s", msg)
        raise ValueError(msg)

    vectors: List[List[float]] = []
    for p in payments:
        try:
            vec, _ = await build_payment_feature_vector(
                db=db,
                payment_input=p,
                org_id=p.org_id,
                created_by_user_id=p.created_by_user_id
            )
            if len(vec) == len(FEATURE_ORDER) and all(isinstance(x, (int, float)) for x in vec):
                vectors.append(vec)
        except Exception:
            logger.warning("Skipping malformed payment record during training.", exc_info=True)
            continue

    if len(vectors) < MIN_TRAINING_SAMPLES:
        msg = f"Valid vector count ({len(vectors)}) is below minimum training threshold ({MIN_TRAINING_SAMPLES})."
        logger.error("ML_TRAINING_FAILED: %s", msg)
        raise ValueError(msg)

    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        max_samples="auto",
        random_state=42,
        n_jobs=-1
    )

    model.fit(vectors)

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    metadata: Dict[str, Any] = {
        "feature_count": len(FEATURE_ORDER),
        "rows_used": len(vectors),
        "contamination": 0.05,
        "trained_at": datetime.now(timezone.utc).isoformat()
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info("ML_TRAINING_COMPLETED: Model artifact saved successfully.")
    return metadata