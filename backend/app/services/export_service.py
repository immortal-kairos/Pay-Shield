import csv
from pathlib import Path
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.payment import Payment
from app.schemas.export import ExportPaymentsRequest

class ExportService:
    EXPORT_DIR = Path("/tmp/payshield_exports")

    @classmethod
    def ensure_export_dir(cls) -> None:
        cls.EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    async def generate_payments_csv(
        cls,
        db: AsyncSession,
        org_id: UUID,
        job_id: UUID,
        filters: ExportPaymentsRequest
    ) -> str:
        cls.ensure_export_dir()
        
        # Base query enforcing org_id scope
        query = select(Payment).options(selectinload(Payment.vendor)).where(Payment.org_id == org_id)
        
        if filters.start_date:
            query = query.where(Payment.payment_date >= filters.start_date)
        if filters.end_date:
            query = query.where(Payment.payment_date <= filters.end_date)
        if filters.status:
            query = query.where(Payment.status == filters.status)
            
        query = query.order_by(Payment.payment_date.desc(), Payment.created_at.desc())
        
        result = await db.execute(query)
        payments = result.scalars().all()
        
        file_path = cls.EXPORT_DIR / f"{job_id}.csv"
        
        # Write CSV natively without locking main thread
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Strict column order
            writer.writerow([
                "Payment ID", "Vendor Name", "Amount", "Currency", 
                "Payment Date", "Status", "Risk Level", "Risk Score", "Created At"
            ])
            
            for p in payments:
                vendor_name = p.vendor.name if p.vendor else "Unknown Vendor"
                writer.writerow([
                    str(p.id),
                    vendor_name,
                    str(p.amount),
                    p.currency,
                    p.payment_date.isoformat() if p.payment_date else "",
                    p.status.value if hasattr(p.status, 'value') else str(p.status),
                    p.risk_level or "",
                    str(p.risk_score) if p.risk_score is not None else "",
                    p.created_at.isoformat() if p.created_at else ""
                ])
                
        return str(file_path)
        