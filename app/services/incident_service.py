from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.check import Check
from app.models.incident import Incident


async def reconcile_incident_for_check(
    db: AsyncSession,
    check: Check,
) -> Incident | None:

    result = await db.execute(
        select(Incident)
        .where(
            Incident.monitor_id == check.monitor_id,
            Incident.is_resolved.is_(False),
        )
        .with_for_update()
    )
    incident = result.scalar_one_or_none()

    if check.is_success:
        if incident is None:
            return None

        incident.status = "resolved"
        incident.is_resolved = True
        incident.resolved_at = datetime.now(timezone.utc)
        return incident

    if incident is not None:
        return incident

    reason = check.error
    if reason is None and check.status_code is not None:
        reason = f"HTTP {check.status_code}"

    incident = Incident(
        monitor_id=check.monitor_id,
        status="open",
        is_resolved=False,
        reason=reason,
    )
    db.add(incident)
    return incident


async def get_monitor_incidents(
    db: AsyncSession,
    monitor_id: int,
) -> list[Incident]:
    result = await db.execute(
        select(Incident)
        .where(Incident.monitor_id == monitor_id)
        .order_by(Incident.started_at.desc())
    )
    return list(result.scalars().all())
