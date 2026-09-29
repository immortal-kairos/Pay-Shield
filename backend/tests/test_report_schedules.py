import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import patch
from httpx import AsyncClient

from app.models.report_schedule import ReportSchedule
from app.models.user import User, UserRole
from app.core.security import create_access_token

@pytest.fixture
async def local_admin_token(db_session, org_id):
    admin_id = uuid4()
    u = User(id=admin_id, org_id=org_id, email=f"admin_{uuid4()}@test.com", password_hash="hash", role=UserRole.ADMIN, is_active=True)
    db_session.add(u)
    await db_session.commit()
    return create_access_token(data={"sub": str(u.id), "email": u.email, "role": "ADMIN", "org_id": str(org_id)})

@pytest.mark.asyncio
async def test_admin_can_create_daily_schedule(async_client: AsyncClient, local_admin_token):
    payload = {"name": "Daily Rep", "export_type": "payments", "frequency": "DAILY", "recipient_emails": ["a@test.com"]}
    res = await async_client.post("/api/analytics/report-schedules", json=payload, headers={"Authorization": f"Bearer {local_admin_token}"})
    assert res.status_code == 201
    data = res.json()
    assert data["frequency"] == "DAILY"
    
    # FIXED: Force timezone to UTC to prevent SQLite parsing clash
    next_run = datetime.fromisoformat(data["next_run_at"]).replace(tzinfo=timezone.utc)
    assert (next_run - datetime.now(timezone.utc)).total_seconds() > 23 * 3600

@pytest.mark.asyncio
async def test_admin_can_create_weekly_schedule(async_client: AsyncClient, local_admin_token):
    payload = {"name": "Weekly Rep", "export_type": "payments", "frequency": "WEEKLY", "recipient_emails": ["a@test.com"]}
    res = await async_client.post("/api/analytics/report-schedules", json=payload, headers={"Authorization": f"Bearer {local_admin_token}"})
    assert res.status_code == 201
    
    # FIXED: Force timezone to UTC
    next_run = datetime.fromisoformat(res.json()["next_run_at"]).replace(tzinfo=timezone.utc)
    assert (next_run - datetime.now(timezone.utc)).total_seconds() > 6 * 24 * 3600

@pytest.mark.asyncio
async def test_maker_cannot_create_schedule(async_client: AsyncClient, maker_token):
    payload = {"name": "Rep", "export_type": "payments", "frequency": "DAILY", "recipient_emails": ["a@test.com"]}
    res = await async_client.post("/api/analytics/report-schedules", json=payload, headers={"Authorization": f"Bearer {maker_token}"})
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_checker_cannot_create_schedule(async_client: AsyncClient, checker_token):
    payload = {"name": "Rep", "export_type": "payments", "frequency": "DAILY", "recipient_emails": ["a@test.com"]}
    res = await async_client.post("/api/analytics/report-schedules", json=payload, headers={"Authorization": f"Bearer {checker_token}"})
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_list_schedules_is_org_scoped(async_client: AsyncClient, local_admin_token, db_session, org_id, user_id):
    s1 = ReportSchedule(org_id=org_id, created_by_user_id=user_id, name="S1", export_type="payments", frequency="DAILY", recipient_emails=["a@a.com"], next_run_at=datetime.now(timezone.utc))
    s2 = ReportSchedule(org_id=uuid4(), created_by_user_id=user_id, name="S2", export_type="payments", frequency="DAILY", recipient_emails=["b@b.com"], next_run_at=datetime.now(timezone.utc))
    db_session.add_all([s1, s2])
    await db_session.commit()

    res = await async_client.get("/api/analytics/report-schedules", headers={"Authorization": f"Bearer {local_admin_token}"})
    data = res.json()
    assert len(data) >= 1
    assert any(d["id"] == str(s1.id) for d in data)
    assert not any(d["id"] == str(s2.id) for d in data)

@pytest.mark.asyncio
async def test_delete_schedule_soft_deletes(async_client: AsyncClient, local_admin_token, db_session, org_id, user_id):
    s1 = ReportSchedule(org_id=org_id, created_by_user_id=user_id, name="S1", export_type="payments", frequency="DAILY", recipient_emails=["a@a.com"], next_run_at=datetime.now(timezone.utc))
    db_session.add(s1)
    await db_session.commit()

    res = await async_client.delete(f"/api/analytics/report-schedules/{s1.id}", headers={"Authorization": f"Bearer {local_admin_token}"})
    assert res.status_code == 200

    await db_session.refresh(s1)
    assert s1.is_active == False

@pytest.mark.asyncio
async def test_run_due_generates_export_and_sends_emails(async_client: AsyncClient, local_admin_token, db_session, org_id, user_id):
    now_utc = datetime.now(timezone.utc)
    s1 = ReportSchedule(org_id=org_id, created_by_user_id=user_id, name="S1", export_type="payments", frequency="DAILY", recipient_emails=["a@a.com", "b@b.com"], next_run_at=now_utc - timedelta(hours=1))
    db_session.add(s1)
    await db_session.commit()

    with patch('app.services.export_service.ExportService.generate_payments_csv') as mock_export:
        with patch('app.services.alert_service.EmailAlertService._send_email') as mock_email:
            res = await async_client.post("/api/analytics/report-schedules/run-due", headers={"Authorization": f"Bearer {local_admin_token}"})
            assert res.status_code == 200
            data = res.json()
            assert data["processed"] == 1
            assert data["emails_sent"] == 2
            mock_export.assert_called_once()
            assert mock_email.call_count == 2

    await db_session.refresh(s1)
    assert s1.last_run_at is not None
    # FIXED: Re-attach tzinfo to SQLite output before comparing
    assert s1.next_run_at.replace(tzinfo=timezone.utc) > now_utc

@pytest.mark.asyncio
async def test_run_due_skips_inactive_schedules(async_client: AsyncClient, local_admin_token, db_session, org_id, user_id):
    s1 = ReportSchedule(org_id=org_id, created_by_user_id=user_id, name="S1", export_type="payments", frequency="DAILY", recipient_emails=["a@a.com"], next_run_at=datetime.now(timezone.utc) - timedelta(hours=1), is_active=False)
    db_session.add(s1)
    await db_session.commit()

    res = await async_client.post("/api/analytics/report-schedules/run-due", headers={"Authorization": f"Bearer {local_admin_token}"})
    assert res.json()["processed"] == 0

@pytest.mark.asyncio
async def test_run_due_continues_on_email_failure(async_client: AsyncClient, local_admin_token, db_session, org_id, user_id):
    s1 = ReportSchedule(org_id=org_id, created_by_user_id=user_id, name="S1", export_type="payments", frequency="DAILY", recipient_emails=["fail@a.com", "success@b.com"], next_run_at=datetime.now(timezone.utc) - timedelta(hours=1))
    db_session.add(s1)
    await db_session.commit()

    # FIXED: Mock must be an async function to match the await in the service
    async def mock_send(email, subject, body):
        if email == "fail@a.com":
            raise Exception("Fail")

    with patch('app.services.export_service.ExportService.generate_payments_csv'):
        with patch('app.services.alert_service.EmailAlertService._send_email', side_effect=mock_send):
            res = await async_client.post("/api/analytics/report-schedules/run-due", headers={"Authorization": f"Bearer {local_admin_token}"})
            assert res.json()["processed"] == 1
            assert res.json()["emails_sent"] == 1

@pytest.mark.asyncio
async def test_invalid_frequency_returns_400(async_client: AsyncClient, local_admin_token):
    payload = {"name": "M", "export_type": "payments", "frequency": "MONTHLY", "recipient_emails": ["a@a.com"]}
    res = await async_client.post("/api/analytics/report-schedules", json=payload, headers={"Authorization": f"Bearer {local_admin_token}"})
    assert res.status_code == 400
    assert res.json()["error"] == "INVALID_FREQUENCY"

@pytest.mark.asyncio
async def test_invalid_export_type_returns_400(async_client: AsyncClient, local_admin_token):
    payload = {"name": "M", "export_type": "vendors", "frequency": "DAILY", "recipient_emails": ["a@a.com"]}
    res = await async_client.post("/api/analytics/report-schedules", json=payload, headers={"Authorization": f"Bearer {local_admin_token}"})
    assert res.status_code == 400
    assert res.json()["error"] == "INVALID_EXPORT_TYPE"

@pytest.mark.asyncio
async def test_empty_recipient_list_returns_400(async_client: AsyncClient, local_admin_token):
    payload = {"name": "M", "export_type": "payments", "frequency": "DAILY", "recipient_emails": []}
    res = await async_client.post("/api/analytics/report-schedules", json=payload, headers={"Authorization": f"Bearer {local_admin_token}"})
    assert res.status_code == 400
    assert res.json()["error"] == "EMPTY_RECIPIENT_LIST"