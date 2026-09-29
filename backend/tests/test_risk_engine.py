import pytest
from datetime import datetime, date, timedelta, timezone
from app.services.risk_engine import evaluate, RiskInput

def base_input():
    return RiskInput(
        amount=50000.0,
        payment_date=date(2026, 6, 15),
        created_at=datetime(2026, 6, 10, 8, 0, tzinfo=timezone.utc), # 13:30 IST (Business hours)
        vendor_bank_account_updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        vendor_prior_approved_payments=5
    )

def test_r01_recent_bank_change_flags_correctly():
    data = base_input()
    data.vendor_bank_account_updated_at = data.created_at - timedelta(days=10)
    res = evaluate(data)
    assert 'RECENT_BANK_CHANGE' in res.flags
    assert res.score == 40

def test_r01_old_bank_change_no_flag():
    data = base_input()
    res = evaluate(data)
    assert 'RECENT_BANK_CHANGE' not in res.flags

def test_r02_high_value_flags_correctly():
    data = base_input()
    data.amount = 1500000.0
    res = evaluate(data)
    assert 'HIGH_VALUE' in res.flags
    assert res.score == 20

def test_r02_below_threshold_no_flag():
    data = base_input()
    res = evaluate(data)
    assert 'HIGH_VALUE' not in res.flags

def test_r03_new_vendor_flags_correctly():
    data = base_input()
    data.vendor_prior_approved_payments = 0
    res = evaluate(data)
    assert 'NEW_VENDOR_PAYMENT' in res.flags
    assert res.score == 20

def test_r03_established_vendor_no_flag():
    data = base_input()
    res = evaluate(data)
    assert 'NEW_VENDOR_PAYMENT' not in res.flags

def test_r04_same_day_payment_flags_correctly():
    data = base_input()
    data.payment_date = data.created_at.date()
    res = evaluate(data)
    assert 'URGENT_PAYMENT' in res.flags
    assert res.score == 10

def test_r04_future_payment_no_flag():
    data = base_input()
    res = evaluate(data)
    assert 'URGENT_PAYMENT' not in res.flags

def test_r05_off_hours_flags_correctly():
    # Test before 9 AM IST (e.g., 2 AM UTC = 7:30 AM IST)
    data = base_input()
    data.created_at = datetime(2026, 6, 10, 2, 0, tzinfo=timezone.utc)
    res = evaluate(data)
    assert 'OFF_HOURS' in res.flags

    # Test after 7 PM IST (e.g., 15 PM UTC = 20:30 PM IST)
    data.created_at = datetime(2026, 6, 10, 15, 0, tzinfo=timezone.utc)
    res2 = evaluate(data)
    assert 'OFF_HOURS' in res2.flags

def test_r05_business_hours_no_flag():
    data = base_input() # 8:00 UTC = 13:30 IST
    res = evaluate(data)
    assert 'OFF_HOURS' not in res.flags

def test_all_rules_triggered_score_is_100():
    data = RiskInput(
        amount=2000000.0, # +20
        payment_date=date(2026, 6, 10), # +10
        created_at=datetime(2026, 6, 10, 2, 0, tzinfo=timezone.utc), # +10 (Off hours)
        vendor_bank_account_updated_at=datetime(2026, 6, 5, tzinfo=timezone.utc), # +40
        vendor_prior_approved_payments=0 # +20
    )
    res = evaluate(data)
    assert res.score == 100 # Capped
    assert res.level == 'HIGH'
    assert len(res.flags) == 5

def test_no_rules_triggered_score_is_zero_level_low():
    data = base_input()
    res = evaluate(data)
    assert res.score == 0
    assert res.level == 'LOW'
    assert len(res.flags) == 0

def test_score_30_is_medium():
    data = base_input()
    data.payment_date = data.created_at.date() # +10
    data.vendor_prior_approved_payments = 1 # +20
    res = evaluate(data)
    assert res.score == 30
    assert res.level == 'MEDIUM'

def test_score_60_is_high():
    data = base_input()
    data.vendor_bank_account_updated_at = data.created_at - timedelta(days=1) # +40
    data.vendor_prior_approved_payments = 0 # +20
    res = evaluate(data)
    assert res.score == 60
    assert res.level == 'HIGH'