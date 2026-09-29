import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy import select
from app.models.audit_log import AuditLog, AuditEventType
from app.services.audit_log_service import AuditLogService

@pytest.mark.asyncio
async def test_audit_log_write_creates_entry(db_session, org_id, user_id):
    await AuditLogService.write(
        db_session, org_id, AuditEventType.USER_LOGIN, "user", user_id, user_id, {"ip": "127.0.0.1"}
    )
    result = await db_session.execute(select(AuditLog))
    log = result.scalars().first()
    assert log is not None
    assert log.event_type == "USER_LOGIN"

@pytest.mark.asyncio
async def test_audit_log_entry_not_updatable(db_session, org_id, user_id):
    await AuditLogService.write(db_session, org_id, AuditEventType.USER_LOGIN, "user", user_id, user_id)
    await db_session.commit()
    
    result = await db_session.execute(select(AuditLog))
    log = result.scalars().first()
    
    with pytest.raises(NotImplementedError):
        log.event_type = "HACKED"
        await db_session.commit()

@pytest.mark.asyncio
async def test_audit_log_entry_not_deletable(db_session, org_id, user_id):
    await AuditLogService.write(db_session, org_id, AuditEventType.USER_LOGIN, "user", user_id, user_id)
    await db_session.commit()
    
    result = await db_session.execute(select(AuditLog))
    log = result.scalars().first()
    
    with pytest.raises(NotImplementedError):
        await db_session.delete(log)
        await db_session.commit()

@pytest.mark.asyncio
async def test_admin_can_read_audit_log(async_client: AsyncClient, admin_token):
    res = await async_client.get("/api/audit-log", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_maker_cannot_read_audit_log(async_client: AsyncClient, maker_token):
    res = await async_client.get("/api/audit-log", headers={"Authorization": f"Bearer {maker_token}"})
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_checker_cannot_read_audit_log(async_client: AsyncClient, checker_token):
    res = await async_client.get("/api/audit-log", headers={"Authorization": f"Bearer {checker_token}"})
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_filter_by_entity_type_returns_correct_entries(async_client: AsyncClient, admin_token, db_session, org_id, user_id):
    await AuditLogService.write(db_session, org_id, AuditEventType.VENDOR_CREATED, "vendor", uuid4(), user_id)
    await AuditLogService.write(db_session, org_id, AuditEventType.PAYMENT_CREATED, "payment", uuid4(), user_id)
    await db_session.commit()

    res = await async_client.get("/api/audit-log?entity_type=vendor", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["entity_type"] == "vendor"

@pytest.mark.asyncio
async def test_pagination_returns_correct_page(async_client: AsyncClient, admin_token, db_session, org_id, user_id):
    for _ in range(5):
        await AuditLogService.write(db_session, org_id, AuditEventType.USER_LOGIN, "user", uuid4(), user_id)
    await db_session.commit()

    res1 = await async_client.get("/api/audit-log?page=1&page_size=2", headers={"Authorization": f"Bearer {admin_token}"})
    res2 = await async_client.get("/api/audit-log?page=2&page_size=2", headers={"Authorization": f"Bearer {admin_token}"})
    
    assert res1.json()["page"] == 1
    assert len(res1.json()["items"]) == 2
    assert res2.json()["page"] == 2
    assert res1.json()["items"][0]["id"] != res2.json()["items"][0]["id"]
    