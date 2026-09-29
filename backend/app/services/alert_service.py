from enum import Enum
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import BackgroundTasks
import sendgrid
from sendgrid.helpers.mail import Mail

from app.core.config import settings
from app.models.payment import Payment
from app.models.user import User, UserRole
from app.models.sent_alert import SentAlert
from app.models.audit_log import AuditEventType
from app.services.audit_log_service import AuditLogService

class AlertType(str, Enum):
    CREATION_CHECKER = 'CREATION_CHECKER'
    APPROVAL_MAKER = 'APPROVAL_MAKER'
    REJECTION_MAKER = 'REJECTION_MAKER'

class EmailAlertService:
    @staticmethod
    async def _send_email(to_email: str, subject: str, html_body: str) -> dict:
        message = Mail(
            from_email=settings.ALERT_SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_body
        )
        try:
            sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            # Execute synchronously in a background thread if using a blocking client, 
            # though SendGrid Python is blocking by default. For simplicity in this async wrapper:
            response = sg.send(message)
            return {"message_id": response.headers.get('X-Message-Id', 'sg-unknown'), "provider": "SendGrid"}
        except Exception as e:
            raise e

    @staticmethod
    async def _record_sent_alert(db: AsyncSession, payment_id: UUID, recipient_id: UUID, alert_type: str):
        alert = SentAlert(
            payment_id=payment_id,
            recipient_user_id=recipient_id,
            alert_type=alert_type,
            sent_at=datetime.now(timezone.utc)
        )
        db.add(alert)
        await db.commit()

    @classmethod
    async def queue_payment_creation_alert(cls, payment: Payment, db: AsyncSession, background_tasks: BackgroundTasks) -> None:
        if payment.status.value != 'PENDING_APPROVAL':
            return
            
        checkers_res = await db.execute(select(User).where(User.org_id == payment.org_id, User.role == UserRole.CHECKER, User.is_active == True))
        checkers = checkers_res.scalars().all()

        for checker in checkers:
            existing = await db.execute(
                select(SentAlert).where(
                    SentAlert.payment_id == payment.id,
                    SentAlert.recipient_user_id == checker.id,
                    SentAlert.alert_type == AlertType.CREATION_CHECKER.value
                )
            )
            if existing.scalar_one_or_none():
                continue

            background_tasks.add_task(cls._send_email_for_creation_checker, db=db, payment=payment, checker_user=checker)

    @classmethod
    async def _send_email_for_creation_checker(cls, db: AsyncSession, payment: Payment, checker_user: User) -> None:
        vendor_name = payment.vendor_name if hasattr(payment, 'vendor_name') else "Vendor"
        amount = f"{payment.currency} {payment.amount:,.2f}"
        high_risk_text = f"<br><b>⚠️ This payment carries a HIGH risk score. Please review carefully. Risk score: {payment.risk_score}</b>" if payment.risk_level == 'HIGH' else ""
        
        subject = f"[PayShield Alert] Payment Created - {vendor_name}"
        html_body = f"""
        <p>A new payment requires your review.</p>
        <ul>
            <li><b>Vendor Name:</b> {vendor_name}</li>
            <li><b>Amount:</b> {amount}</li>
            <li><b>Scheduled Date:</b> {payment.payment_date}</li>
            <li><b>Risk Level:</b> {payment.risk_level} {high_risk_text}</li>
        </ul>
        """
        
        try:
            res = await cls._send_email(checker_user.email, subject, html_body)
            await cls._record_sent_alert(db, payment.id, checker_user.id, AlertType.CREATION_CHECKER.value)
            await AuditLogService.write(db, payment.org_id, AuditEventType.EMAIL_ALERT_SENT, 'payment', payment.id, checker_user.id, {
                "to_email": checker_user.email,
                "message_id": res.get("message_id"),
                "provider": res.get("provider")
            })
        except Exception as exc:
            await AuditLogService.write(db, payment.org_id, AuditEventType.EMAIL_ALERT_FAILED, 'payment', payment.id, checker_user.id, {
                "to_email": checker_user.email,
                "error": str(exc)
            })

    @classmethod
    async def queue_payment_review_alert(cls, payment: Payment, db: AsyncSession, background_tasks: BackgroundTasks) -> None:
        maker_res = await db.execute(select(User).where(User.id == payment.created_by_user_id))
        maker = maker_res.scalars().first()
        if not maker:
            return

        if payment.status.value == 'APPROVED':
            alert_type = AlertType.APPROVAL_MAKER.value
            target_method = cls._send_email_for_approval_maker
        elif payment.status.value == 'REJECTED':
            alert_type = AlertType.REJECTION_MAKER.value
            target_method = cls._send_email_for_rejection_maker
        else:
            return

        existing = await db.execute(
            select(SentAlert).where(
                SentAlert.payment_id == payment.id,
                SentAlert.recipient_user_id == maker.id,
                SentAlert.alert_type == alert_type
            )
        )
        if existing.scalar_one_or_none():
            return

        background_tasks.add_task(target_method, db=db, payment=payment, maker_user=maker)

    @classmethod
    async def _send_email_for_approval_maker(cls, db: AsyncSession, payment: Payment, maker_user: User) -> None:
        vendor_name = payment.vendor.name if payment.vendor else "Vendor"
        
        checker_res = await db.execute(select(User).where(User.id == payment.reviewed_by_user_id))
        checker = checker_res.scalars().first()
        checker_email = checker.email if checker else "Unknown Checker"

        subject = f"[PayShield Alert] Payment Approved - {vendor_name}"
        html_body = f"""
        <p>Your payment has been approved.</p>
        <ul>
            <li><b>Vendor Name:</b> {vendor_name}</li>
            <li><b>Amount:</b> {payment.currency} {payment.amount:,.2f}</li>
            <li><b>Scheduled Date:</b> {payment.payment_date}</li>
            <li><b>Risk Level:</b> {payment.risk_level}</li>
            <li><b>Action By:</b> {checker_email}</li>
        </ul>
        """
        
        try:
            res = await cls._send_email(maker_user.email, subject, html_body)
            await cls._record_sent_alert(db, payment.id, maker_user.id, AlertType.APPROVAL_MAKER.value)
            await AuditLogService.write(db, payment.org_id, AuditEventType.EMAIL_ALERT_SENT, 'payment', payment.id, maker_user.id, {"to_email": maker_user.email})
        except Exception as exc:
            await AuditLogService.write(db, payment.org_id, AuditEventType.EMAIL_ALERT_FAILED, 'payment', payment.id, maker_user.id, {"to_email": maker_user.email, "error": str(exc)})

    @classmethod
    async def _send_email_for_rejection_maker(cls, db: AsyncSession, payment: Payment, maker_user: User) -> None:
        vendor_name = payment.vendor.name if payment.vendor else "Vendor"
        
        checker_res = await db.execute(select(User).where(User.id == payment.reviewed_by_user_id))
        checker = checker_res.scalars().first()
        checker_email = checker.email if checker else "Unknown Checker"

        subject = f"[PayShield Alert] Payment Rejected - {vendor_name}"
        html_body = f"""
        <p>Your payment has been rejected.</p>
        <ul>
            <li><b>Vendor Name:</b> {vendor_name}</li>
            <li><b>Amount:</b> {payment.currency} {payment.amount:,.2f}</li>
            <li><b>Scheduled Date:</b> {payment.payment_date}</li>
            <li><b>Action By:</b> {checker_email}</li>
            <li><b>Rejection Reason:</b> {payment.rejection_reason}</li>
        </ul>
        """
        
        try:
            res = await cls._send_email(maker_user.email, subject, html_body)
            await cls._record_sent_alert(db, payment.id, maker_user.id, AlertType.REJECTION_MAKER.value)
            await AuditLogService.write(db, payment.org_id, AuditEventType.EMAIL_ALERT_SENT, 'payment', payment.id, maker_user.id, {"to_email": maker_user.email})
        except Exception as exc:
            await AuditLogService.write(db, payment.org_id, AuditEventType.EMAIL_ALERT_FAILED, 'payment', payment.id, maker_user.id, {"to_email": maker_user.email, "error": str(exc)})