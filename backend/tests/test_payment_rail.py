import pytest
import json
from uuid import uuid4
from datetime import date, timedelta
from fastapi import BackgroundTasks
from unittest.mock import patch, MagicMock
from app.models.payment import Payment, PaymentStatus
from app.models.vendor import Vendor, VendorStatus
from app.models.audit_log import AuditLog, AuditEventType
from app.services.payment_service import approve_payment
from app.core.errors import PayShieldError
from sqlalchemy.future import select

# MOCK DATA
FAKE_PAYOUT_ID = "pout_Fake12345"

@pytest.fixture
def mock_razorpay():
    with patch('razorpay.Client') as mock_client:
        instance = mock_client.return_value
        instance.payout.create.return_value = {"id": FAKE_PAYOUT_ID, "status": "queued"}
        yield instance

@pytest.fixture
async def setup_payment_for_rail(db_session, user_id, org_id):
    vendor = Vendor(
        org_id=org_id, name="Rail Vendor", contact_email="v@rail.com",
        bank_account_hash="hash", bank_account_last4="1234",
        bank_account_encrypted="encrypted_account_data",
        ifsc_code="HDFC0001", status=VendorStatus.ACTIVE,
        created_by_user_id=user_id
    )
    db_session.add(vendor)
    await db_session.commit()
    await db_session.refresh(vendor)

    payment = Payment(
        org_id=org_id, vendor_id=vendor.id, amount=1000.0,
        currency="INR", payment_date=date(2026, 6, 1),
        status=PaymentStatus.PENDING_APPROVAL,
        risk_score=10, risk_level="LOW",
        created_by_user_id=user_id
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)
    return payment, vendor

@pytest.mark.asyncio
async def test_approval_triggers_background_transfer_initiation(db_session, setup_payment_for_rail, checker_user_id, mock_razorpay):
    payment, vendor = setup_payment_for_rail
    bg_tasks = BackgroundTasks()
    
    current_user = {"id": checker_user_id, "org_id": payment.org_id, "role": "CHECKER"}
    
    with patch('app.services.payment_service.encryption.decrypt', return_value="1234567890"):
        res = await approve_payment(db_session, payment.id, current_user, bg_tasks, skip_totp_check=True)
        
        # Find the specific transfer task instead of relying on index 0
        transfer_task = next(t for t in bg_tasks.tasks if t.func.__name__ == '_initiate_transfer')
        await transfer_task.func(*transfer_task.args, **transfer_task.kwargs)

    assert res.status == PaymentStatus.APPROVED
    assert any(t.func.__name__ == '_initiate_transfer' for t in bg_tasks.tasks)

    await db_session.refresh(payment)
    assert payment.transfer_status == 'INITIATED'
    assert payment.provider_reference_id == FAKE_PAYOUT_ID

@pytest.mark.asyncio
async def test_razorpay_api_failure_sets_transfer_failed(db_session, setup_payment_for_rail, checker_user_id):
    payment, vendor = setup_payment_for_rail
    bg_tasks = BackgroundTasks()
    current_user = {"id": checker_user_id, "org_id": payment.org_id, "role": "CHECKER"}

    with patch('app.services.payment_service.encryption.decrypt', return_value="1234567890"):
        res = await approve_payment(db_session, payment.id, current_user, bg_tasks, skip_totp_check=True)
        
        with patch('app.services.payment_rail_service.PaymentRailService.initiate_payout', side_effect=PayShieldError(502, "Error", "Razorpay down")):
            transfer_task = next(t for t in bg_tasks.tasks if t.func.__name__ == '_initiate_transfer')
            await transfer_task.func(*transfer_task.args, **transfer_task.kwargs)

    await db_session.refresh(payment)
    assert payment.transfer_status == 'FAILED'
    assert payment.transfer_failure_reason == "Razorpay down"

@pytest.mark.asyncio
async def test_transfer_failure_does_not_change_approved_status(db_session, setup_payment_for_rail, checker_user_id):
    payment, vendor = setup_payment_for_rail
    bg_tasks = BackgroundTasks()
    current_user = {"id": checker_user_id, "org_id": payment.org_id, "role": "CHECKER"}

    with patch('app.services.payment_service.encryption.decrypt', return_value="1234567890"):
        await approve_payment(db_session, payment.id, current_user, bg_tasks, skip_totp_check=True)
        with patch('app.services.payment_rail_service.PaymentRailService.initiate_payout', side_effect=PayShieldError(502, "Error", "Fail")):
            transfer_task = next(t for t in bg_tasks.tasks if t.func.__name__ == '_initiate_transfer')
            await transfer_task.func(*transfer_task.args, **transfer_task.kwargs)

    await db_session.refresh(payment)
    assert payment.status == PaymentStatus.APPROVED

@pytest.mark.asyncio
async def test_missing_encrypted_account_sets_transfer_failed_gracefully(db_session, setup_payment_for_rail, checker_user_id):
    payment, vendor = setup_payment_for_rail
    vendor.bank_account_encrypted = None 
    await db_session.commit()

    bg_tasks = BackgroundTasks()
    current_user = {"id": checker_user_id, "org_id": payment.org_id, "role": "CHECKER"}

    res = await approve_payment(db_session, payment.id, current_user, bg_tasks, skip_totp_check=True)
    
    assert res.transfer_status == 'FAILED'
    assert res.status == PaymentStatus.APPROVED
    # Assert the transfer task was NEVER queued, even if email tasks were
    assert not any(t.func.__name__ == '_initiate_transfer' for t in bg_tasks.tasks)

@pytest.mark.asyncio
async def test_idempotency_key_is_payment_id(db_session, setup_payment_for_rail, checker_user_id, mock_razorpay):
    payment, vendor = setup_payment_for_rail
    bg_tasks = BackgroundTasks()
    current_user = {"id": checker_user_id, "org_id": payment.org_id, "role": "CHECKER"}

    with patch('app.services.payment_service.encryption.decrypt', return_value="1234567890"):
        await approve_payment(db_session, payment.id, current_user, bg_tasks, skip_totp_check=True)
        transfer_task = next(t for t in bg_tasks.tasks if t.func.__name__ == '_initiate_transfer')
        await transfer_task.func(*transfer_task.args, **transfer_task.kwargs)

    mock_razorpay.payout.create.assert_called_once()
    call_args = mock_razorpay.payout.create.call_args
    assert call_args[0][1]["idempotency_key"] == str(payment.id)

@pytest.mark.asyncio
async def test_amount_converted_to_paise(db_session, setup_payment_for_rail, checker_user_id, mock_razorpay):
    payment, vendor = setup_payment_for_rail
    payment.amount = 1000.00
    await db_session.commit()
    
    bg_tasks = BackgroundTasks()
    current_user = {"id": checker_user_id, "org_id": payment.org_id, "role": "CHECKER"}

    with patch('app.services.payment_service.encryption.decrypt', return_value="1234567890"):
        await approve_payment(db_session, payment.id, current_user, bg_tasks, skip_totp_check=True)
        transfer_task = next(t for t in bg_tasks.tasks if t.func.__name__ == '_initiate_transfer')
        await transfer_task.func(*transfer_task.args, **transfer_task.kwargs)

    call_args = mock_razorpay.payout.create.call_args
    payload = call_args[0][0]
    assert payload["amount"] == 100000 

@pytest.mark.asyncio
async def test_webhook_valid_signature_processes_payout_processed(async_client, db_session, setup_payment_for_rail):
    payment, _ = setup_payment_for_rail
    payment.provider_reference_id = FAKE_PAYOUT_ID
    await db_session.commit()

    payload = {"event": "payout.processed", "payload": {"payout": {"entity": {"id": FAKE_PAYOUT_ID}}}}

    with patch('app.services.payment_rail_service.PaymentRailService.verify_webhook_signature', return_value=True):
        res = await async_client.post("/api/webhooks/razorpay", json=payload, headers={"x-razorpay-signature": "valid"})

    assert res.status_code == 200
    await db_session.refresh(payment)
    assert payment.transfer_status == 'SUCCESS'

@pytest.mark.asyncio
async def test_webhook_invalid_signature_returns_400(async_client):
    payload = {"event": "payout.processed"}
    with patch('app.services.payment_rail_service.PaymentRailService.verify_webhook_signature', return_value=False):
        res = await async_client.post("/api/webhooks/razorpay", json=payload, headers={"x-razorpay-signature": "invalid"})
    assert res.status_code == 400

@pytest.mark.asyncio
async def test_webhook_payout_failed_sets_transfer_failed(async_client, db_session, setup_payment_for_rail):
    payment, _ = setup_payment_for_rail
    payment.provider_reference_id = FAKE_PAYOUT_ID
    await db_session.commit()

    payload = {"event": "payout.failed", "payload": {"payout": {"entity": {"id": FAKE_PAYOUT_ID, "failure_reason": "Insufficient balance"}}}}

    with patch('app.services.payment_rail_service.PaymentRailService.verify_webhook_signature', return_value=True):
        res = await async_client.post("/api/webhooks/razorpay", json=payload, headers={"x-razorpay-signature": "valid"})

    assert res.status_code == 200
    await db_session.refresh(payment)
    assert payment.transfer_status == 'FAILED'
    assert payment.transfer_failure_reason == "Insufficient balance"

@pytest.mark.asyncio
async def test_webhook_idempotent_duplicate_event_not_reprocessed(async_client, db_session, setup_payment_for_rail):
    payment, _ = setup_payment_for_rail
    payment.provider_reference_id = FAKE_PAYOUT_ID
    await db_session.commit()

    payload = {"event": "payout.processed", "payload": {"payout": {"entity": {"id": FAKE_PAYOUT_ID}}}}

    with patch('app.services.payment_rail_service.PaymentRailService.verify_webhook_signature', return_value=True):
        await async_client.post("/api/webhooks/razorpay", json=payload, headers={"x-razorpay-signature": "valid"})
        await async_client.post("/api/webhooks/razorpay", json=payload, headers={"x-razorpay-signature": "valid"})

    result = await db_session.execute(select(AuditLog).where(AuditLog.entity_id == payment.id, AuditLog.event_type == AuditEventType.PAYMENT_TRANSFER_SUCCESS.value))
    records = result.scalars().all()
    assert len(records) == 1

@pytest.mark.asyncio
async def test_webhook_unknown_event_returns_200_silently(async_client):
    payload = {"event": "payout.queued"} 
    with patch('app.services.payment_rail_service.PaymentRailService.verify_webhook_signature', return_value=True):
        res = await async_client.post("/api/webhooks/razorpay", json=payload, headers={"x-razorpay-signature": "valid"})
    assert res.status_code == 200