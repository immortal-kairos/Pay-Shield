import uuid
import logging
from datetime import datetime, date, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate
from app.ml.feature_builder import build_payment_feature_vector
from app.ml.model_service import model_service

logger = logging.getLogger("payshield.payment")

def _parse_date(d: Any) -> date:
    if isinstance(d, str):
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except ValueError:
            return datetime.now(timezone.utc).date()
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return datetime.now(timezone.utc).date()

async def create_payment(
    db: AsyncSession,
    schema: PaymentCreate,
    org_id: Any,
    user_id: Any
) -> Payment:
    rule_risk_score = 0.0
    rule_risk_level = "LOW"
    rule_risk_flags = []

    ml_score = None
    ml_label = None
    snapshot = None
    ml_ready = False

    try:
        vector, snapshot = await build_payment_feature_vector(
            db=db,
            payment_input=schema,
            org_id=org_id,
            created_by_user_id=user_id
        )

        if model_service.is_model_ready():
            scoring_res = model_service.score_payment(vector)
            if scoring_res.get("ml_available"):
                ml_score = scoring_res.get("ml_risk_score")
                ml_label = scoring_res.get("ml_risk_label")
                ml_ready = True
    except Exception:
        logger.exception("ML_SCORING_FAILED: Non-fatal scoring exception caught.")
        ml_score = None
        ml_label = None
        snapshot = None
        ml_ready = False

    p_date_raw = getattr(schema, "payment_date", None) or getattr(schema, "execution_date", None)
    ref_note = getattr(schema, "reference_note", None) or getattr(schema, "notes", None)

    vendor_uuid = schema.vendor_id if isinstance(schema.vendor_id, uuid.UUID) else uuid.UUID(str(schema.vendor_id))
    org_uuid = org_id if isinstance(org_id, uuid.UUID) else uuid.UUID(str(org_id))
    user_uuid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))

    new_payment = Payment(
        org_id=org_uuid,
        vendor_id=vendor_uuid,
        amount=float(schema.amount),
        currency=schema.currency,
        payment_date=_parse_date(p_date_raw),
        reference_note=ref_note,
        status=PaymentStatus.PENDING_APPROVAL,
        risk_score=rule_risk_score,
        risk_level=rule_risk_level,
        risk_flags=rule_risk_flags,
        created_by_user_id=user_uuid,
        ml_risk_score=ml_score,
        ml_risk_label=ml_label,
        ml_feature_snapshot=snapshot,
        ml_available=ml_ready
    )

    db.add(new_payment)
    await db.commit()
    await db.refresh(new_payment)
    return new_payment