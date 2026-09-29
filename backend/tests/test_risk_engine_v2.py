import pytest
from uuid import uuid4
from datetime import date, datetime, timedelta, timezone
from app.services.risk_engine import evaluate, RiskInput
from app.models.payment import Payment, PaymentStatus

def get_base_input():
    return RiskInput(
        amount=1000.0,
        currency='INR',
        payment_date=date(2026, 6, 1),
        created_at=datetime.now(timezone.utc),
        vendor_bank_account_updated_at=datetime.now(timezone.utc) - timedelta(days=10),
        vendor_prior_approved_payments=5,
        org_id=uuid4(),
        maker_user_id=uuid4(),
        vendor_id=uuid4()
    )

@pytest.mark.asyncio
async def test_r06_vendor_velocity_flags_correctly(db_session):
    org_id = uuid4()
    vendor_id = uuid4()
    now = datetime.now(timezone.utc)
    
    # 3 prior approved payments in last 24h
    for _ in range(3):
        p = Payment(org_id=org_id, vendor_id=vendor_id, amount=100.0, currency="INR", payment_date=now.date(), status=PaymentStatus.APPROVED, risk_score=0, risk_level="LOW", created_by_user_id=uuid4(), created_at=now - timedelta(hours=2))
        db_session.add(p)
    await db_session.commit()

    inp = get_base_input()
    inp.org_id = org_id
    inp.vendor_id = vendor_id
    inp.created_at = now

    res = await evaluate(inp, db=db_session)
    assert 'VELOCITY_VENDOR' in res.flags
    assert res.score >= 25

@pytest.mark.asyncio
async def test_r06_below_threshold_no_flag(db_session):
    org_id = uuid4()
    vendor_id = uuid4()
    now = datetime.now(timezone.utc)
    
    # Only 2 prior approved payments
    for _ in range(2):
        p = Payment(org_id=org_id, vendor_id=vendor_id, amount=100.0, currency="INR", payment_date=now.date(), status=PaymentStatus.APPROVED, risk_score=0, risk_level="LOW", created_by_user_id=uuid4(), created_at=now - timedelta(hours=2))
        db_session.add(p)
    await db_session.commit()

    inp = get_base_input()
    inp.org_id = org_id
    inp.vendor_id = vendor_id
    inp.created_at = now

    res = await evaluate(inp, db=db_session)
    assert 'VELOCITY_VENDOR' not in res.flags

@pytest.mark.asyncio
async def test_r07_maker_velocity_flags_correctly(db_session):
    org_id = uuid4()
    maker_id = uuid4()
    now = datetime.now(timezone.utc)
    
    # 5 prior payments by maker in last 1 hour
    for _ in range(5):
        p = Payment(org_id=org_id, vendor_id=uuid4(), amount=100.0, currency="INR", payment_date=now.date(), status=PaymentStatus.PENDING_APPROVAL, risk_score=0, risk_level="LOW", created_by_user_id=maker_id, created_at=now - timedelta(minutes=30))
        db_session.add(p)
    await db_session.commit()

    inp = get_base_input()
    inp.org_id = org_id
    inp.maker_user_id = maker_id
    inp.created_at = now

    res = await evaluate(inp, db=db_session)
    assert 'VELOCITY_MAKER' in res.flags
    assert res.score >= 20

@pytest.mark.asyncio
async def test_r07_below_threshold_no_flag(db_session):
    org_id = uuid4()
    maker_id = uuid4()
    now = datetime.now(timezone.utc)
    
    # Only 4 prior payments by maker
    for _ in range(4):
        p = Payment(org_id=org_id, vendor_id=uuid4(), amount=100.0, currency="INR", payment_date=now.date(), status=PaymentStatus.PENDING_APPROVAL, risk_score=0, risk_level="LOW", created_by_user_id=maker_id, created_at=now - timedelta(minutes=30))
        db_session.add(p)
    await db_session.commit()

    inp = get_base_input()
    inp.org_id = org_id
    inp.maker_user_id = maker_id
    inp.created_at = now

    res = await evaluate(inp, db=db_session)
    assert 'VELOCITY_MAKER' not in res.flags

@pytest.mark.asyncio
async def test_r08_near_cap_flags_correctly():
    inp = get_base_input()
    inp.amount = 48_00_000.0  # Above 47,50,000 threshold
    res = await evaluate(inp, db=None)
    assert 'NEAR_CAP_AMOUNT' in res.flags

@pytest.mark.asyncio
async def test_r08_below_threshold_no_flag():
    inp = get_base_input()
    inp.amount = 47_00_000.0  # Below 47,50,000 threshold
    res = await evaluate(inp, db=None)
    assert 'NEAR_CAP_AMOUNT' not in res.flags

@pytest.mark.asyncio
async def test_velocity_rules_skipped_when_db_is_none(db_session):
    # Setup data that WOULD trigger R-07 if DB was present
    org_id = uuid4()
    maker_id = uuid4()
    now = datetime.now(timezone.utc)
    
    for _ in range(5):
        p = Payment(org_id=org_id, vendor_id=uuid4(), amount=100.0, currency="INR", payment_date=now.date(), status=PaymentStatus.PENDING_APPROVAL, risk_score=0, risk_level="LOW", created_by_user_id=maker_id, created_at=now - timedelta(minutes=30))
        db_session.add(p)
    await db_session.commit()

    inp = get_base_input()
    inp.org_id = org_id
    inp.maker_user_id = maker_id
    inp.created_at = now

    # Pass None for db
    res = await evaluate(inp, db=None)
    assert 'VELOCITY_MAKER' not in res.flags

@pytest.mark.asyncio
async def test_all_sprint1_rules_still_pass_with_db_none():
    inp = get_base_input()
    # Force an R-01 state to prove base engine still evaluates
    inp.vendor_prior_approved_payments = 0
    res = await evaluate(inp, db=None)
    
    # FIXED: Was 'NEW_VENDOR', now 'NEW_VENDOR_PAYMENT'
    assert 'NEW_VENDOR_PAYMENT' in res.flags
    assert 'VELOCITY_VENDOR' not in res.flags
    