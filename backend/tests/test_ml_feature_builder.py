import pytest
from unittest.mock import MagicMock
from app.ml.feature_builder import build_payment_feature_vector, FEATURE_ORDER

@pytest.mark.asyncio
async def test_feature_builder_returns_stable_vector_shape(db_session):
    mock_payment = MagicMock()
    mock_payment.amount = 250000.0
    mock_payment.currency = "INR"
    mock_payment.payment_date = "2026-08-20"
    mock_payment.vendor_id = "00000000-0000-0000-0000-000000000001"

    vector, snapshot = await build_payment_feature_vector(
        db_session,
        mock_payment,
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003"
    )
    assert len(vector) == 15
    assert len(vector) == len(FEATURE_ORDER)
    assert len(snapshot) == 15

@pytest.mark.asyncio
async def test_feature_builder_has_no_null_values(db_session):
    mock_payment = MagicMock()
    mock_payment.amount = 5000.0
    mock_payment.currency = "GBP"
    mock_payment.payment_date = None
    mock_payment.vendor_id = None

    vector, snapshot = await build_payment_feature_vector(
        db_session,
        mock_payment,
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003"
    )
    for val in vector:
        assert val is not None
        assert isinstance(val, (int, float))