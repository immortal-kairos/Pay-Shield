from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime, date, timedelta, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.payment import Payment, PaymentStatus

@dataclass
class RiskInput:
    amount: float
    payment_date: date
    created_at: datetime
    vendor_bank_account_updated_at: Optional[datetime]
    vendor_prior_approved_payments: int
    # Default values appended to preserve backward compatibility for V1 tests
    currency: str = 'INR'
    org_id: Optional[UUID] = None
    maker_user_id: Optional[UUID] = None
    vendor_id: Optional[UUID] = None

@dataclass
class RiskResult:
    score: int
    flags: List[str]
    level: str

    # Magic method to make the synchronous object awaitable!
    # This allows V2 tests to `await evaluate()` while V1 tests `evaluate()` synchronously.
    def __await__(self):
        async def _yield_self():
            return self
        return _yield_self().__await__()

# --- Sprint 1: Stateless Pure Functions (Restored to exact V1 specs) ---

def _check_r01_recent_bank_change(input: RiskInput) -> Tuple[bool, int, str]:
    if input.vendor_bank_account_updated_at:
        delta = input.created_at - input.vendor_bank_account_updated_at
        if delta.days < 30: 
            return True, 40, 'RECENT_BANK_CHANGE'
    return False, 0, ''

def _check_r02_high_value(input: RiskInput) -> Tuple[bool, int, str]:
    if input.amount >= 1000000.0:
        return True, 20, 'HIGH_VALUE'
    return False, 0, ''

def _check_r03_new_vendor(input: RiskInput) -> Tuple[bool, int, str]:
    if input.vendor_prior_approved_payments <= 1:
        return True, 20, 'NEW_VENDOR_PAYMENT'
    return False, 0, ''

def _check_r04_same_day_payment(input: RiskInput) -> Tuple[bool, int, str]:
    if input.payment_date == input.created_at.date():
        return True, 10, 'URGENT_PAYMENT'
    return False, 0, ''

def _check_r05_off_hours(input: RiskInput) -> Tuple[bool, int, str]:
    # IST Business Hours check (9 AM to 6 PM)
    hour_ist = (input.created_at + timedelta(hours=5, minutes=30)).hour
    if hour_ist < 9 or hour_ist >= 18:
        return True, 10, 'OFF_HOURS'
    return False, 0, ''


# --- Sprint 2: Extended Rules (R-06 to R-08) ---

async def _check_r06_vendor_velocity(db: AsyncSession, input: RiskInput) -> Tuple[bool, int, str]:
    if not input.org_id or not input.vendor_id or not input.created_at:
        return False, 0, ''
    
    cutoff_time = input.created_at - timedelta(hours=24)
    query = select(func.count()).where(
        Payment.org_id == input.org_id,
        Payment.vendor_id == input.vendor_id,
        Payment.status == PaymentStatus.APPROVED,
        Payment.created_at >= cutoff_time,
        Payment.created_at <= input.created_at
    )
    result = await db.execute(query)
    count = result.scalar() or 0
    
    if count >= 3:
        return True, 25, 'VELOCITY_VENDOR'
    return False, 0, ''

async def _check_r07_maker_velocity(db: AsyncSession, input: RiskInput) -> Tuple[bool, int, str]:
    if not input.org_id or not input.maker_user_id or not input.created_at:
        return False, 0, ''

    cutoff_time = input.created_at - timedelta(hours=1)
    query = select(func.count()).where(
        Payment.org_id == input.org_id,
        Payment.created_by_user_id == input.maker_user_id,
        Payment.created_at >= cutoff_time,
        Payment.created_at <= input.created_at
    )
    result = await db.execute(query)
    count = result.scalar() or 0
    
    if count >= 5:
        return True, 20, 'VELOCITY_MAKER'
    return False, 0, ''

def _check_r08_near_cap_amount(input: RiskInput) -> Tuple[bool, int, str]:
    cap = 5000000 # Indian numbering: 50 Lakhs (5,000,000)
    threshold = 0.95 * cap
    if input.amount >= threshold:
        return True, 15, 'NEAR_CAP_AMOUNT'
    return False, 0, ''

# --- Core Evaluation Engine ---

def _finalize(score: int, flags: List[str]) -> RiskResult:
    score = min(score, 100)
    if score >= 60:
        level = "HIGH"
    elif score >= 30:
        level = "MEDIUM"
    else:
        level = "LOW"
    return RiskResult(score=score, flags=flags, level=level)

async def _evaluate_async(input: RiskInput, db: AsyncSession, base_score: int, base_flags: List[str]) -> RiskResult:
    score = base_score
    flags = base_flags.copy()
    try:
        r06_ok, r06_score, r06_flag = await _check_r06_vendor_velocity(db, input)
        if r06_ok:
            score += r06_score
            flags.append(r06_flag)

        r07_ok, r07_score, r07_flag = await _check_r07_maker_velocity(db, input)
        if r07_ok:
            score += r07_score
            flags.append(r07_flag)
    except Exception:
        pass # Engine must never raise exceptions
        
    return _finalize(score, flags)

def evaluate(input: RiskInput, db: AsyncSession | None = None):
    score = 0
    flags = []

    # 1. Evaluate Stateless Rules (Sync)
    pure_rules = [
        _check_r01_recent_bank_change,
        _check_r02_high_value,
        _check_r03_new_vendor,
        _check_r04_same_day_payment,
        _check_r05_off_hours,
        _check_r08_near_cap_amount
    ]

    for rule in pure_rules:
        is_flagged, rule_score, rule_flag = rule(input)
        if is_flagged:
            score += rule_score
            flags.append(rule_flag)

    # 2. Return path
    if db is not None:
        # Returns a real Coroutine that the app/v2 tests must await
        return _evaluate_async(input, db, score, flags)
        
    # Returns the Awaitable RiskResult (fully backward compatible with synchronous V1 tests)
    return _finalize(score, flags)