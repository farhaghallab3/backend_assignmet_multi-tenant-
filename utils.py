from sqlalchemy.ext.asyncio import AsyncSession
from models import AuditLog

async def create_audit_log(
    db: AsyncSession,
    org_id: int,
    user_id: int,
    action: str,
    details: str
):
    log = AuditLog(
        org_id=org_id,
        user_id=user_id,
        action=action,
        details=details
    )
    db.add(log)
    await db.commit()
