import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Tuple, List, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.payment import Payment
from app.models.vendor import Vendor

FEATURE_ORDER: List[str] = [
    "amount",
    "currency_code_encoded",
    "execution_day_of_week",
    "execution_day_of_month",
    "lead_time_days",
    "vendor_age_days",
    "maker_payment_count_30d",
    "vendor_payment_count_30d",
    "maker_avg_amount_30d",
    "vendor_avg_amount_30d",
    "amount_vs_maker_avg_ratio",
    "amount_vs_vendor_avg_ratio",
    "recent_org_payment_count_24h",
    "is_new_vendor_flag",
    "is_high_amount_flag"
]

def encode_currency(currency: str) -> float:
    mapping = {"INR": 1.0, "USD": 2.0, "EUR": 3.0}
    return mapping.get(str(currency).upper(), 0.0)

def safe_ratio(numerator: float, denominator: float, fallback: float = 1.0) -> float:
    if denominator <= 0.0:
        return fallback
    return numerator / denominator

def _to_uuid(val: Any) -> Union[uuid.UUID, None]:
    if isinstance(val, uuid.UUID):
        return val
    if isinstance(val, str):
        try:
            return uuid.UUID(val)
        except ValueError:
            return None
    return None

def _extract_dates(payment_input: Any) -> Tuple[datetime, date]:
    created_at = getattr(payment_input, "created_at", None)
    if not isinstance(created_at, datetime):
        created_at = datetime.now(timezone.utc)

    exec_val = getattr(payment_input, "payment_date", None) or getattr(payment_input, "execution_date", None)
    if isinstance(exec_val, str):
        try:
            execution_date = datetime.strptime(exec_val, "%Y-%m-%d").date()
        except ValueError:
            execution_date = created_at.date()
    elif isinstance(exec_val, datetime):
        execution_date = exec_val.date()
    elif isinstance(exec_val, date):
        execution_date = exec_val
    else:
        execution_date = created_at.date()

    return created_at, execution_date

async def build_payment_feature_vector(
    db: AsyncSession,
    payment_input: Any,
    org_id: Any,
    created_by_user_id: Any
) -> Tuple[List[float], Dict[str, Any]]:
    created_at, execution_date = _extract_dates(payment_input)
    amount = float(getattr(payment_input, "amount", 0.0))
    currency = getattr(payment_input, "currency", "INR")
    vendor_id_raw = getattr(payment_input, "vendor_id", None)

    vendor_uuid = _to_uuid(vendor_id_raw)
    org_uuid = _to_uuid(org_id)
    user_uuid = _to_uuid(created_by_user_id)

    # 1. Base & Calendar
    currency_encoded = encode_currency(currency)
    exec_day_of_week = float(execution_date.weekday())
    exec_day_of_month = float(execution_date.day)

    created_date = created_at.date()
    lead_time_days = max(0.0, float((execution_date - created_date).days))

    # 2. Vendor context
    vendor = None
    if vendor_uuid and db:
        result = await db.execute(select(Vendor).where(Vendor.id == vendor_uuid))
        vendor = result.scalar_one_or_none()

    if vendor and getattr(vendor, "created_at", None):
        v_created = vendor.created_at
        v_date = v_created.date() if isinstance(v_created, datetime) else v_created
        vendor_age_days = max(0.0, float((created_date - v_date).days))
        is_new_vendor = 1.0 if vendor_age_days < 30.0 else 0.0
    else:
        vendor_age_days = 365.0
        is_new_vendor = 0.0

    # 3. 30-Day Aggregates
    thirty_days_ago = created_at - timedelta(days=30)
    maker_count_30d = 0.0
    maker_avg_amount_30d = 0.0
    if user_uuid and db:
        maker_stmt = select(
            func.count(Payment.id),
            func.coalesce(func.avg(Payment.amount), 0.0)
        ).where(
            Payment.created_by_user_id == user_uuid,
            Payment.created_at >= thirty_days_ago,
            Payment.created_at < created_at
        )
        maker_res = (await db.execute(maker_stmt)).first()
        if maker_res:
            maker_count_30d = float(maker_res[0] or 0.0)
            maker_avg_amount_30d = float(maker_res[1] or 0.0)

    vendor_count_30d = 0.0
    vendor_avg_amount_30d = 0.0
    if vendor_uuid and db:
        vendor_stmt = select(
            func.count(Payment.id),
            func.coalesce(func.avg(Payment.amount), 0.0)
        ).where(
            Payment.vendor_id == vendor_uuid,
            Payment.created_at >= thirty_days_ago,
            Payment.created_at < created_at
        )
        vendor_res = (await db.execute(vendor_stmt)).first()
        if vendor_res:
            vendor_count_30d = float(vendor_res[0] or 0.0)
            vendor_avg_amount_30d = float(vendor_res[1] or 0.0)

    # 4. Ratios
    amount_vs_maker_ratio = safe_ratio(amount, maker_avg_amount_30d, fallback=1.0)
    amount_vs_vendor_ratio = safe_ratio(amount, vendor_avg_amount_30d, fallback=1.0)

    # 5. Org 24-Hour Velocity
    twenty_four_hours_ago = created_at - timedelta(hours=24)
    org_count_24h = 0.0
    if org_uuid and db:
        org_stmt = select(func.count(Payment.id)).where(
            Payment.org_id == org_uuid,
            Payment.created_at >= twenty_four_hours_ago,
            Payment.created_at < created_at
        )
        org_count_24h = float((await db.execute(org_stmt)).scalar() or 0.0)

    is_high_amount = 1.0 if amount >= 1_000_000.0 else 0.0

    snapshot: Dict[str, Any] = {
        "amount": amount,
        "currency_code_encoded": currency_encoded,
        "execution_day_of_week": exec_day_of_week,
        "execution_day_of_month": exec_day_of_month,
        "lead_time_days": lead_time_days,
        "vendor_age_days": vendor_age_days,
        "maker_payment_count_30d": maker_count_30d,
        "vendor_payment_count_30d": vendor_count_30d,
        "maker_avg_amount_30d": maker_avg_amount_30d,
        "vendor_avg_amount_30d": vendor_avg_amount_30d,
        "amount_vs_maker_avg_ratio": amount_vs_maker_ratio,
        "amount_vs_vendor_avg_ratio": amount_vs_vendor_ratio,
        "recent_org_payment_count_24h": org_count_24h,
        "is_new_vendor_flag": is_new_vendor,
        "is_high_amount_flag": is_high_amount
    }

    vector: List[float] = [float(snapshot[feat]) for feat in FEATURE_ORDER]
    return vector, snapshot