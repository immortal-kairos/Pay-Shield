import pytest
from backend.app.ml.model_service import ModelService

def test_model_service_scores_vector_gracefully_when_unloaded():
    service = ModelService()
    # Ensure unready state returns non-throwing fallback
    res = service.score_payment([1.0] * 15)
    assert res == {"ml_available": False}