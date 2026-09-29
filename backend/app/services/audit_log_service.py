from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog, AuditEventType

class AuditLogService:
    @staticmethod
    async def write(
        db: AsyncSession,
        org_id: UUID,
        event_type: AuditEventType,
        entity_type: str,
        entity_id: UUID,
        actor_user_id: UUID,
        metadata: dict = None
    ) -> None:
        log_entry = AuditLog(
            org_id=org_id,
            event_type=event_type.value if hasattr(event_type, "value") else event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            metadata_=metadata or {}
        )
        db.add(log_entry)
        # Flush to ensure it's written within the current transaction
        await db.flush()