import pytest
from datetime import date
from httpx import AsyncClient
from uuid import uuid4
from app.models.payment import Payment, PaymentStatus
from app.models.vendor import Vendor, VendorStatus

@pytest.mark.asyncio
async def test_dashboard_metrics_returns_correct_aggregations(async_client: AsyncClient, checker_token, db_session, org_id, user_id):
    # Setup Vendors
    v1 = Vendor(org_id=org_id, name="Vendor A", contact_email="a@a.com", bank_account_last4="1111", bank_account_hash="h1", ifsc_code="I1", status=VendorStatus.ACTIVE, created_by_user_id=user_id)
    v2 = Vendor(org_id=org_id, name="Vendor B", contact_email="b@b.com", bank_account_last4="2222", bank_account_hash="h2", ifsc_code="I2", status=VendorStatus.ACTIVE, created_by_user_id=user_id)
    db_session.add_all([v1, v2])
    await db_session.commit()

    # Setup Payments
    p1 = Payment(org_id=org_id, vendor_id=v1.id, amount=1000.0, currency="INR", payment_date=date.today(), status=PaymentStatus.APPROVED, risk_score=10, risk_level="LOW", created_by_user_id=user_id)
    p2 = Payment(org_id=org_id, vendor_id=v1.id, amount=2000.0, currency="INR", payment_date=date.today(), status=PaymentStatus.APPROVED, risk_score=10, risk_level="LOW", created_by_user_id=user_id)
    p3 = Payment(org_id=org_id, vendor_id=v2.id, amount=500.0, currency="INR", payment_date=date.today(), status=PaymentStatus.PENDING_APPROVAL, risk_score=80, risk_level="HIGH", created_by_user_id=user_id)
    db_session.add_all([p1, p2, p3])
    await db_session.commit()

    # Test API
    res = await async_client.get("/api/analytics/dashboard", headers={"Authorization": f"Bearer {checker_token}"})
    assert res.status_code == 200
    data = res.json()

    assert data["total_volume_inr"] == 3000.0
    assert data["payment_count_by_status"]["APPROVED"] == 2
    assert data["payment_count_by_status"]["PENDING_APPROVAL"] == 1
    assert data["high_risk_payments_count"] == 1
    assert data["top_vendors_by_volume"][0]["vendor_name"] == "Vendor A"
    assert data["top_vendors_by_volume"][0]["total_volume"] == 3000.0

@pytest.mark.asyncio
async def test_dashboard_respects_org_isolation(async_client: AsyncClient, checker_token, db_session, org_id, user_id):
    # Setup Payment in a DIFFERENT org
    other_org_id = uuid4()
    p_other = Payment(org_id=other_org_id, vendor_id=uuid4(), amount=9999.0, currency="INR", payment_date=date.today(), status=PaymentStatus.APPROVED, risk_score=10, risk_level="LOW", created_by_user_id=user_id)
    db_session.add(p_other)
    await db_session.commit()

    res = await async_client.get("/api/analytics/dashboard", headers={"Authorization": f"Bearer {checker_token}"})
    data = res.json()
    assert data["total_volume_inr"] == 0.0 # Should not see the 9999.0

@pytest.mark.asyncio
async def test_maker_cannot_access_dashboard(async_client: AsyncClient, maker_token):
    res = await async_client.get("/api/analytics/dashboard", headers={"Authorization": f"Bearer {maker_token}"})
    assert res.status_code == 403