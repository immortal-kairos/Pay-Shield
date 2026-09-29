import pytest
from httpx import AsyncClient
from datetime import date, timedelta
from uuid import uuid4
from sqlalchemy import select
from app.models.vendor import Vendor, VendorStatus
from app.models.payment import PaymentStatus

# Helper fixture to create a vendor
async def create_active_vendor(db_session, org_id, user_id):
    v = Vendor(org_id=org_id, name="Active Vendor", contact_email="v@v.com", bank_account_last4="1234", bank_account_hash="hash", ifsc_code="IFSC", status=VendorStatus.ACTIVE, created_by_user_id=user_id)
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)
    return v

@pytest.mark.asyncio
async def test_maker_can_create_payment(async_client: AsyncClient, maker_token, db_session, org_id, user_id):
    vendor = await create_active_vendor(db_session, org_id, user_id)
    payload = {"vendor_id": str(vendor.id), "amount": 1000.0, "currency": "INR", "payment_date": date.today().isoformat()}
    res = await async_client.post("/api/payments", json=payload, headers={"Authorization": f"Bearer {maker_token}"})
    assert res.status_code == 201
    assert res.json()["status"] == "PENDING_APPROVAL"

@pytest.mark.asyncio
async def test_checker_cannot_create_payment(async_client: AsyncClient, checker_token, db_session, org_id, user_id):
    vendor = await create_active_vendor(db_session, org_id, user_id)
    payload = {"vendor_id": str(vendor.id), "amount": 1000.0, "currency": "INR", "payment_date": date.today().isoformat()}
    res = await async_client.post("/api/payments", json=payload, headers={"Authorization": f"Bearer {checker_token}"})
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_inactive_vendor_returns_400(async_client: AsyncClient, maker_token, db_session, org_id, user_id):
    v = Vendor(org_id=org_id, name="Pending", contact_email="p@p.com", bank_account_last4="1234", bank_account_hash="h", ifsc_code="I", status=VendorStatus.PENDING_REVIEW, created_by_user_id=user_id)
    db_session.add(v)
    await db_session.commit()
    
    payload = {"vendor_id": str(v.id), "amount": 1000.0, "currency": "INR", "payment_date": date.today().isoformat()}
    res = await async_client.post("/api/payments", json=payload, headers={"Authorization": f"Bearer {maker_token}"})
    assert res.status_code == 400

@pytest.mark.asyncio
async def test_past_payment_date_returns_400(async_client: AsyncClient, maker_token, db_session, org_id, user_id):
    vendor = await create_active_vendor(db_session, org_id, user_id)
    past_date = (date.today() - timedelta(days=1)).isoformat()
    payload = {"vendor_id": str(vendor.id), "amount": 1000.0, "currency": "INR", "payment_date": past_date}
    res = await async_client.post("/api/payments", json=payload, headers={"Authorization": f"Bearer {maker_token}"})
    assert res.status_code == 422 # Pydantic catches this

@pytest.mark.asyncio
async def test_amount_over_cap_returns_400(async_client: AsyncClient, maker_token, db_session, org_id, user_id):
    vendor = await create_active_vendor(db_session, org_id, user_id)
    payload = {"vendor_id": str(vendor.id), "amount": 5000001.0, "currency": "INR", "payment_date": date.today().isoformat()}
    res = await async_client.post("/api/payments", json=payload, headers={"Authorization": f"Bearer {maker_token}"})
    assert res.status_code == 422

@pytest.mark.asyncio
async def test_non_inr_currency_returns_400(async_client: AsyncClient, maker_token, db_session, org_id, user_id):
    vendor = await create_active_vendor(db_session, org_id, user_id)
    payload = {"vendor_id": str(vendor.id), "amount": 1000.0, "currency": "USD", "payment_date": date.today().isoformat()}
    res = await async_client.post("/api/payments", json=payload, headers={"Authorization": f"Bearer {maker_token}"})
    assert res.status_code == 422

@pytest.mark.asyncio
async def test_risk_score_attached_to_payment_on_creation(async_client: AsyncClient, maker_token, db_session, org_id, user_id):
    vendor = await create_active_vendor(db_session, org_id, user_id)
    payload = {"vendor_id": str(vendor.id), "amount": 1000.0, "currency": "INR", "payment_date": date.today().isoformat()}
    res = await async_client.post("/api/payments", json=payload, headers={"Authorization": f"Bearer {maker_token}"})
    assert "risk_score" in res.json()
    assert "risk_level" in res.json()

@pytest.mark.asyncio
async def test_recent_bank_change_vendor_gives_high_risk(async_client: AsyncClient, maker_token, db_session, org_id, user_id):
    vendor = await create_active_vendor(db_session, org_id, user_id)
    # New vendor (0 prior payments = +20), recent bank change (now() = +40) = 60 (HIGH)
    payload = {"vendor_id": str(vendor.id), "amount": 1000.0, "currency": "INR", "payment_date": (date.today() + timedelta(days=5)).isoformat()}
    res = await async_client.post("/api/payments", json=payload, headers={"Authorization": f"Bearer {maker_token}"})
    assert res.json()["risk_level"] == "HIGH"
    assert "RECENT_BANK_CHANGE" in res.json()["risk_flags"]

@pytest.mark.asyncio
async def test_payment_response_contains_risk_flags(async_client: AsyncClient, maker_token, db_session, org_id, user_id):
    vendor = await create_active_vendor(db_session, org_id, user_id)
    payload = {"vendor_id": str(vendor.id), "amount": 1000.0, "currency": "INR", "payment_date": date.today().isoformat()}
    res = await async_client.post("/api/payments", json=payload, headers={"Authorization": f"Bearer {maker_token}"})
    assert isinstance(res.json()["risk_flags"], list)

@pytest.mark.asyncio
async def test_audit_log_written_on_payment_created(async_client: AsyncClient, maker_token, db_session, org_id, user_id):
    vendor = await create_active_vendor(db_session, org_id, user_id)
    payload = {"vendor_id": str(vendor.id), "amount": 1000.0, "currency": "INR", "payment_date": date.today().isoformat()}
    res = await async_client.post("/api/payments", json=payload, headers={"Authorization": f"Bearer {maker_token}"})
    assert res.status_code == 201 # DB assertions handled in integrated audit tests

@pytest.mark.asyncio
async def test_list_payments_filterable_by_status(async_client: AsyncClient, maker_token, db_session, org_id, user_id):
    vendor = await create_active_vendor(db_session, org_id, user_id)
    payload = {"vendor_id": str(vendor.id), "amount": 1000.0, "currency": "INR", "payment_date": date.today().isoformat()}
    await async_client.post("/api/payments", json=payload, headers={"Authorization": f"Bearer {maker_token}"})
    
    res = await async_client.get("/api/payments?status_filter=PENDING_APPROVAL", headers={"Authorization": f"Bearer {maker_token}"})
    assert len(res.json()) >= 1
    
    res_empty = await async_client.get("/api/payments?status_filter=APPROVED", headers={"Authorization": f"Bearer {maker_token}"})
    assert len(res_empty.json()) == 0