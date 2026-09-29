import pytest
from uuid import uuid4
from datetime import date, datetime, timezone
from unittest.mock import patch
from fastapi import BackgroundTasks
from sqlalchemy.future import select

from app.models.payment import Payment, PaymentStatus
from app.models.vendor import VendorStatus, Vendor
from app.models.user import User, UserRole
from app.models.sent_alert import SentAlert
from app.models.audit_log import AuditLog, AuditEventType
from app.services.alert_service import EmailAlertService, AlertType
from app.services.payment_service import create_payment, approve_payment
from app.schemas.payment import PaymentCreate

@pytest.fixture
async def setup_alert_data(db_session, org_id, user_id):
    vendor = Vendor(
        org_id=org_id, name="Alert Vendor", contact_email="v@v.com",
        bank_account_hash="hash", bank_account_last4="1234",
        bank_account_encrypted="encrypted", ifsc_code="HDFC", 
        status=VendorStatus.ACTIVE, created_by_user_id=user_id
    )
    db_session.add(vendor)
    
    checker_user = User(
        org_id=org_id, email="checker_alert@test.com", password_hash="hash", 
        role=UserRole.CHECKER, is_active=True
    )
    db_session.add(checker_user)
    await db_session.commit()
    await db_session.refresh(vendor)
    await db_session.refresh(checker_user)
    return vendor, checker_user

@pytest.mark.asyncio
async def test_payment_creation_queues_checker_emails(db_session, setup_alert_data, user_id, org_id):
    vendor, checker = setup_alert_data
    bg_tasks = BackgroundTasks()
    current_user = {"id": user_id, "org_id": org_id, "role": "MAKER"}
    payment_in = PaymentCreate(vendor_id=vendor.id, amount=1000.0, currency="INR", payment_date=date(2026, 6, 1))

    with patch('app.services.alert_service.EmailAlertService._send_email', return_value={"message_id": "sg-123", "provider": "SendGrid"}) as mock_send:
        payment = await create_payment(db_session, payment_in, current_user, bg_tasks)
        
        # Execute the background task
        for task in bg_tasks.tasks:
            await task.func(*task.args, **task.kwargs)

    mock_send.assert_called_once()
    assert mock_send.call_args[0][0] == checker.email
    
    # Assert SentAlert recorded
    alert_res = await db_session.execute(select(SentAlert).where(SentAlert.payment_id == payment.id))
    alerts = alert_res.scalars().all()
    assert len(alerts) == 1
    assert alerts[0].alert_type == AlertType.CREATION_CHECKER.value

@pytest.mark.asyncio
async def test_payment_approval_queues_maker_email(db_session, setup_alert_data, user_id, org_id):
    vendor, checker = setup_alert_data
    bg_tasks = BackgroundTasks()
    
    # Create
    current_user_maker = {"id": user_id, "org_id": org_id, "role": "MAKER"}
    payment_in = PaymentCreate(vendor_id=vendor.id, amount=1000.0, currency="INR", payment_date=date(2026, 6, 1))
    payment = await create_payment(db_session, payment_in, current_user_maker, bg_tasks)
    bg_tasks.tasks.clear() # Clear creation tasks

    # Approve
    current_user_checker = {"id": checker.id, "org_id": org_id, "role": "CHECKER"}
    with patch('app.services.payment_service.encryption.decrypt', return_value="1234567890"):
        with patch('app.services.alert_service.EmailAlertService._send_email', return_value={"message_id": "sg-123", "provider": "SendGrid"}) as mock_send:
            await approve_payment(db_session, payment.id, current_user_checker, bg_tasks, skip_totp_check=True)
            
            # Run tasks (Approval email + Payment Rail transfer)
            for task in bg_tasks.tasks:
                if task.func.__name__ == '_send_email_for_approval_maker':
                    await task.func(*task.args, **task.kwargs)

    mock_send.assert_called_once()
    assert mock_send.call_args[0][0] == "maker@test.com" # Maker's email

@pytest.mark.asyncio
async def test_email_provider_failure_does_not_block_flow(db_session, setup_alert_data, user_id, org_id):
    vendor, checker = setup_alert_data
    bg_tasks = BackgroundTasks()
    current_user = {"id": user_id, "org_id": org_id, "role": "MAKER"}
    payment_in = PaymentCreate(vendor_id=vendor.id, amount=1000.0, currency="INR", payment_date=date(2026, 6, 1))

    with patch('app.services.alert_service.EmailAlertService._send_email', side_effect=Exception("500 example")):
        payment = await create_payment(db_session, payment_in, current_user, bg_tasks)
        for task in bg_tasks.tasks:
            await task.func(*task.args, **task.kwargs)

    # Assert payment succeeded despite email error
    assert payment.status == PaymentStatus.PENDING_APPROVAL
    
    # Assert Audit log recorded failure
    audit_res = await db_session.execute(select(AuditLog).where(AuditLog.entity_id == payment.id, AuditLog.event_type == AuditEventType.EMAIL_ALERT_FAILED.value))
    assert audit_res.scalars().first() is not None

@pytest.mark.asyncio
async def test_idempotency_prevents_duplicate_emails(db_session, setup_alert_data, user_id, org_id):
    vendor, checker = setup_alert_data
    bg_tasks = BackgroundTasks()
    
    payment = Payment(org_id=org_id, vendor_id=vendor.id, amount=1000.0, currency="INR", payment_date=date(2026, 6, 1), status=PaymentStatus.PENDING_APPROVAL, risk_score=10, risk_level="LOW", created_by_user_id=user_id)
    db_session.add(payment)
    await db_session.commit()

    # Pre-seed the sent alert
    alert = SentAlert(payment_id=payment.id, recipient_user_id=checker.id, alert_type=AlertType.CREATION_CHECKER.value, sent_at=datetime.now(timezone.utc))
    db_session.add(alert)
    await db_session.commit()

    with patch('app.services.alert_service.EmailAlertService._send_email') as mock_send:
        await EmailAlertService.queue_payment_creation_alert(payment, db_session, bg_tasks)
        for task in bg_tasks.tasks:
            await task.func(*task.args, **task.kwargs)

    mock_send.assert_not_called()

@pytest.mark.asyncio
async def test_high_risk_flag_included_in_checker_email(db_session, setup_alert_data, user_id, org_id):
    vendor, checker = setup_alert_data
    bg_tasks = BackgroundTasks()
    
    # Simulate a high risk score
    payment = Payment(org_id=org_id, vendor_id=vendor.id, amount=1000.0, currency="INR", payment_date=date(2026, 6, 1), status=PaymentStatus.PENDING_APPROVAL, risk_score=80, risk_level="HIGH", created_by_user_id=user_id)
    db_session.add(payment)
    await db_session.commit()

    with patch('app.services.alert_service.EmailAlertService._send_email', return_value={"message_id": "sg", "provider": "sg"}) as mock_send:
        await EmailAlertService.queue_payment_creation_alert(payment, db_session, bg_tasks)
        for task in bg_tasks.tasks:
            await task.func(*task.args, **task.kwargs)

    html_body_sent = mock_send.call_args[0][2]
    assert "HIGH risk score" in html_body_sent
    