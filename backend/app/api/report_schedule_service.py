import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.report_schedule import ReportSchedule
from app.schemas.report_schedule import ReportScheduleCreateRequest
from app.schemas.export import ExportPaymentsRequest
from app.core.errors import PayShieldError, ErrorCode
from app.services.export_service import ExportService
from app.services.alert_service import EmailAlertService
from app.services.audit_log_service import AuditLogService

class ReportScheduleService:
    @classmethod
    async def create_schedule(cls, db: AsyncSession, org_id: uuid.UUID, created_by_user_id: uuid.UUID, payload: ReportScheduleCreateRequest) -> ReportSchedule:
        if payload.export_type != 'payments':
            raise PayShieldError(400, ErrorCode.INVALID_EXPORT_TYPE, "Export type must be 'payments'")
        if payload.frequency not in ['DAILY', 'WEEKLY']:
            raise PayShieldError(400, ErrorCode.INVALID_FREQUENCY, "Frequency must be DAILY or WEEKLY")
        if not payload.recipient_emails:
            raise PayShieldError(400, ErrorCode.EMPTY_RECIPIENT_LIST, "Recipient list cannot be empty")

        now_utc = datetime.now(timezone.utc)
        next_run = now_utc + timedelta(days=1) if payload.frequency == 'DAILY' else now_utc + timedelta(days=7)

        schedule = ReportSchedule(
            org_id=org_id,
            created_by_user_id=created_by_user_id,
            name=payload.name,
            export_type=payload.export_type,
            frequency=payload.frequency,
            recipient_emails=payload.recipient_emails,
            filters=payload.filters,
            is_active=True,
            next_run_at=next_run,
            created_at=now_utc,
            updated_at=now_utc
        )
        db.add(schedule)
        await db.flush()

        await AuditLogService.write(db, org_id, "REPORT_SCHEDULE_CREATED", "report_schedule", schedule.id, created_by_user_id)
        await db.commit()
        await db.refresh(schedule)
        return schedule

    @classmethod
    async def list_schedules(cls, db: AsyncSession, org_id: uuid.UUID):
        query = select(ReportSchedule).where(ReportSchedule.org_id == org_id, ReportSchedule.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def delete_schedule(cls, db: AsyncSession, org_id: uuid.UUID, schedule_id: uuid.UUID):
        query = select(ReportSchedule).where(ReportSchedule.id == schedule_id, ReportSchedule.org_id == org_id)
        result = await db.execute(query)
        schedule = result.scalars().first()

        if not schedule:
            raise PayShieldError(404, ErrorCode.REPORT_SCHEDULE_NOT_FOUND, "Schedule not found")

        schedule.is_active = False
        schedule.updated_at = datetime.now(timezone.utc)
        await AuditLogService.write(db, org_id, "REPORT_SCHEDULE_DELETED", "report_schedule", schedule.id, schedule.created_by_user_id)
        await db.commit()
        return {"status": "deleted"}

    @classmethod
    async def run_due_schedules(cls, db: AsyncSession, base_url: str) -> dict:
        now_utc = datetime.now(timezone.utc)
        query = select(ReportSchedule).where(
            ReportSchedule.is_active == True,
            ReportSchedule.next_run_at <= now_utc
        )
        result = await db.execute(query)
        schedules = result.scalars().all()

        processed = 0
        emails_sent = 0

        for schedule in schedules:
            try:
                job_id = uuid.uuid4()
                filters_obj = ExportPaymentsRequest(**schedule.filters) if schedule.filters else ExportPaymentsRequest()
                
                # 1. Generate CSV
                await ExportService.generate_payments_csv(db, schedule.org_id, job_id, filters_obj)

                download_link = f"{base_url}/api/analytics/exports/{job_id}/download"
                subject = f"[PayShield Report] {schedule.name}"
                body = f"Report: {schedule.name}\nFrequency: {schedule.frequency}\nGenerated At: {now_utc.isoformat()}\nDownload Link: {download_link}"

                # 2. Email Recipients
                for email in schedule.recipient_emails:
                    try:
                        # Reusing synchronous email mock from US-09
                        EmailAlertService._send_email(email, subject, body)
                        emails_sent += 1
                        await AuditLogService.write(db, schedule.org_id, "REPORT_SCHEDULE_EMAIL_SENT", "report_schedule", schedule.id, schedule.created_by_user_id, {"email": email})
                    except Exception as e:
                        await AuditLogService.write(db, schedule.org_id, "REPORT_SCHEDULE_EMAIL_FAILED", "report_schedule", schedule.id, schedule.created_by_user_id, {"email": email, "error": str(e)})

                # 3. Advance Schedule
                schedule.last_run_at = now_utc
                schedule.next_run_at = now_utc + timedelta(days=1) if schedule.frequency == "DAILY" else now_utc + timedelta(days=7)
                schedule.updated_at = now_utc

                await AuditLogService.write(db, schedule.org_id, "REPORT_SCHEDULE_RUN", "report_schedule", schedule.id, schedule.created_by_user_id)
                processed += 1
            except Exception as e:
                await AuditLogService.write(db, schedule.org_id, "REPORT_SCHEDULE_RUN_FAILED", "report_schedule", schedule.id, schedule.created_by_user_id, {"error": str(e)})

        await db.commit()
        return {"processed": processed, "emails_sent": emails_sent}
        