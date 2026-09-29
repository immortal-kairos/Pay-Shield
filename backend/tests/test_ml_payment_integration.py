import pytest
from unittest.mock import patch
from app.services.payment_service import create_payment
from app.schemas.payment import PaymentCreate

@pytest.mark.asyncio
async def test_training_fails_with_insufficient_rows(db_session):
    from app.ml.train_isolation_forest import execute_training_pipeline
    with pytest.raises(ValueError, match="Insufficient training data"):
        await execute_training_pipeline(db_session)

@pytest.mark.asyncio
@patch("app.ml.model_service.model_service.is_model_ready", return_value=False)
async def test_payment_creation_succeeds_when_model_missing(mock_ready, db_session):
    payload = PaymentCreate(
        vendor_id="00000000-0000-0000-0000-000000000001",
        amount=150000.0,
        currency="INR",
        execution_date="2026-08-25",
        notes="Invoice settlement"
    )
    p = await create_payment(
        db_session,
        payload,
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003"
    )
    assert p.id is not None
    assert p.status.value == "PENDING_APPROVAL"
    assert p.ml_available is False
    assert p.ml_risk_score is None

@pytest.mark.asyncio
@patch("app.ml.model_service.model_service.is_model_ready", return_value=True)
@patch("app.ml.model_service.model_service.score_payment")
async def test_payment_creation_returns_ml_fields_when_model_ready(mock_score, mock_ready, db_session):
    mock_score.return_value = {
        "raw_anomaly_score": -0.15,
        "ml_risk_score": 75.5,
        "ml_risk_label": "HIGH",
        "ml_available": True
    }
    payload = PaymentCreate(
        vendor_id="00000000-0000-0000-0000-000000000001",
        amount=9500000.0,
        currency="INR",
        execution_date="2026-08-25",
        notes="High value transfer"
    )
    p = await create_payment(
        db_session,
        payload,
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003"
    )
    assert p.ml_available is True
    assert p.ml_risk_score == 75.5
    assert p.ml_risk_label == "HIGH"
    assert p.ml_feature_snapshot is not None