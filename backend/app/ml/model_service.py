import os
import json
import logging
from typing import Optional, Dict, Any, List
import joblib

logger = logging.getLogger("payshield.ml")

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "isolation_forest.joblib")
METADATA_PATH = os.path.join(ARTIFACT_DIR, "isolation_forest_metadata.json")

class ModelService:
    _instance: Optional['ModelService'] = None

    def __new__(cls) -> 'ModelService':
        if cls._instance is None:
            cls._instance = super(ModelService, cls).__new__(cls)
            cls._instance._model = None
            cls._instance._metadata = {}
            cls._instance._initialized = False
        return cls._instance

    def load_model(self) -> bool:
        try:
            if not os.path.exists(MODEL_PATH):
                logger.warning("ML_MODEL_LOAD_FAILED: Artifact file not found at %s", MODEL_PATH)
                self._model = None
                self._initialized = False
                return False

            self._model = joblib.load(MODEL_PATH)

            if os.path.exists(METADATA_PATH):
                with open(METADATA_PATH, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            else:
                self._metadata = {"feature_count": 15, "trained_at": None}

            self._initialized = True
            logger.info("ML_MODEL_LOAD_SUCCESS: IsolationForest model initialized into memory.")
            return True
        except Exception:
            logger.exception("ML_MODEL_LOAD_FAILED: Unexpected error loading model artifact.")
            self._model = None
            self._initialized = False
            return False

    def is_model_ready(self) -> bool:
        return self._initialized and self._model is not None

    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata

    def get_artifact_path(self) -> str:
        return MODEL_PATH

    def score_payment(self, vector: List[float]) -> Dict[str, Any]:
        if not self.is_model_ready():
            return {"ml_available": False}

        try:
            reshaped = [vector]
            # IsolationForest decision_function outputs lower numbers for anomalies (~ -0.4 to 0.2)
            raw_decision = float(self._model.decision_function(reshaped)[0])

            # Deterministic normalization: map decision_function to [0, 100] where higher = riskier
            # Normal distribution midpoint ~0.15, anomalies <= -0.15
            shifted = (raw_decision - 0.20) / -0.60
            normalized = max(0.0, min(100.0, shifted * 100.0))

            if normalized < 40.0:
                label = "LOW"
            elif normalized < 70.0:
                label = "MEDIUM"
            else:
                label = "HIGH"

            return {
                "raw_anomaly_score": round(raw_decision, 4),
                "ml_risk_score": round(normalized, 2),
                "ml_risk_label": label,
                "ml_available": True
            }
        except Exception:
            logger.exception("ML_SCORING_FAILED: Exception during model inference.")
            return {"ml_available": False}

# Global singleton
model_service = ModelService()