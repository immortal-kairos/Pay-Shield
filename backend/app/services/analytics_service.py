from typing import Optional
from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case, desc
from app.models.payment import Payment, PaymentStatus
from app.models.vendor import Vendor
from app.schemas.analytics import DashboardMetrics, TopVendor

async def get_dashboard_metrics(db: AsyncSession, org_id: UUID, start_date: Optional[date] = None, end_date: Optional[date] = None) -> DashboardMetrics:
    
    # Base query filter for organization
    base_filters = [Payment.org_id == org_id]
    if start_date:
        base_filters.append(Payment.payment_date >= start_date)
    if end_date:
        base_filters.append(Payment.payment_date <= end_date)

    # 1. Total Volume (APPROVED or SUCCESS)
    volume_query = select(func.sum(Payment.amount)).where(
        *base_filters,
        Payment.status == PaymentStatus.APPROVED  # Assuming SUCCESS is handled similarly or maps to APPROVED
    )
    volume_result = await db.execute(volume_query)
    total_volume = volume_result.scalar() or 0.0

    # 2. Payment Count by Status
    status_query = select(Payment.status, func.count(Payment.id)).where(*base_filters).group_by(Payment.status)
    status_result = await db.execute(status_query)
    status_counts = {status.value: count for status, count in status_result.all()}

    # 3. High Risk Payments Count
    high_risk_query = select(func.count(Payment.id)).where(
        *base_filters,
        Payment.risk_level == "HIGH"
    )
    high_risk_result = await db.execute(high_risk_query)
    high_risk_count = high_risk_result.scalar() or 0

    # 4. Top Vendors by Volume
    top_vendors_query = (
        select(Vendor.name, func.sum(Payment.amount).label("volume"))
        .join(Vendor, Payment.vendor_id == Vendor.id)
        .where(*base_filters, Payment.status == PaymentStatus.APPROVED)
        .group_by(Vendor.name)
        .order_by(desc("volume"))
        .limit(3)
    )
    top_vendors_result = await db.execute(top_vendors_query)
    
    top_vendors = [
        TopVendor(vendor_name=row[0], total_volume=row[1]) 
        for row in top_vendors_result.all()
    ]

    return DashboardMetrics(
        total_volume_inr=float(total_volume),
        payment_count_by_status=status_counts,
        high_risk_payments_count=high_risk_count,
        top_vendors_by_volume=top_vendors
    )