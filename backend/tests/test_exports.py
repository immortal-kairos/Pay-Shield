import pytest
import uuid
import csv
from pathlib import Path
from datetime import date
from httpx import AsyncClient

from app.models.payment import Payment, PaymentStatus
from app.models.vendor import Vendor, VendorStatus
from app.services.export_service import ExportService
from app.schemas.export import ExportPaymentsRequest

@pytest.fixture(autouse=True)
def setup_export_dir():
    # Ensure dir exists before tests run
    ExportService.ensure_export_dir()
    yield

@pytest.mark.asyncio
async def test_export_triggers_background_task_and_returns_202(async_client: AsyncClient, checker_token):
    payload = {"start_date": "2026-06-01", "end_date": "2026-06-30", "status": "APPROVED"}
    
    res = await async_client.post("/api/analytics/exports/payments", json=payload, headers={"Authorization": f"Bearer {checker_token}"})
    
    assert res.status_code == 202
    data = res.json()
    assert "job_id" in data
    assert data["status"] == "queued"

@pytest.mark.asyncio
async def test_download_export_returns_file(async_client: AsyncClient, checker_token):
    job_id = uuid.uuid4()
    file_path = ExportService.EXPORT_DIR / f"{job_id}.csv"
    
    # Dummy seed
    with open(file_path, "w") as f:
        f.write("Payment ID,Vendor Name\n123,Vendor A\n")
        
    res = await async_client.get(f"/api/analytics/exports/{job_id}/download", headers={"Authorization": f"Bearer {checker_token}"})
    
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "123,Vendor A" in res.text
    
    # Cleanup
    file_path.unlink(missing_ok=True)

@pytest.mark.asyncio
async def test_maker_cannot_trigger_export(async_client: AsyncClient, maker_token):
    res = await async_client.post("/api/analytics/exports/payments", json={}, headers={"Authorization": f"Bearer {maker_token}"})
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_export_filters_by_org_only(db_session, org_id, user_id):
    v1 = Vendor(org_id=org_id, name="My Vendor", contact_email="v1@v.com", bank_account_last4="1111", bank_account_hash="h1", ifsc_code="I1", status=VendorStatus.ACTIVE, created_by_user_id=user_id)
    db_session.add(v1)
    await db_session.commit()
    
    p1 = Payment(org_id=org_id, vendor_id=v1.id, amount=100.0, currency="INR", payment_date=date.today(), status=PaymentStatus.APPROVED, risk_score=10, risk_level="LOW", created_by_user_id=user_id)
    
    other_org = uuid.uuid4()
    p2 = Payment(org_id=other_org, vendor_id=v1.id, amount=999.0, currency="INR", payment_date=date.today(), status=PaymentStatus.APPROVED, risk_score=10, risk_level="LOW", created_by_user_id=user_id)
    db_session.add_all([p1, p2])
    await db_session.commit()
    
    job_id = uuid.uuid4()
    filters = ExportPaymentsRequest()
    
    # Trigger generation manually to verify internal service logic
    await ExportService.generate_payments_csv(db_session, org_id, job_id, filters)
    
    file_path = ExportService.EXPORT_DIR / f"{job_id}.csv"
    with open(file_path, "r") as f:
        content = f.read()
        
    assert "100.0" in content
    assert "999.0" not in content
    
    file_path.unlink(missing_ok=True)

@pytest.mark.asyncio
async def test_invalid_date_range_returns_400(async_client: AsyncClient, checker_token):
    payload = {"start_date": "2026-06-30", "end_date": "2026-06-01"}
    res = await async_client.post("/api/analytics/exports/payments", json=payload, headers={"Authorization": f"Bearer {checker_token}"})
    
    assert res.status_code == 400
    data = res.json()
    assert data["error"] == "INVALID_DATE_RANGE"

@pytest.mark.asyncio
async def test_download_missing_file_returns_404(async_client: AsyncClient, checker_token):
    job_id = uuid.uuid4()
    res = await async_client.get(f"/api/analytics/exports/{job_id}/download", headers={"Authorization": f"Bearer {checker_token}"})
    
    assert res.status_code == 404
    data = res.json()
    assert data["error"] == "EXPORT_FILE_NOT_FOUND"