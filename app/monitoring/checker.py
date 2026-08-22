import time

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.check import Check
from app.models.monitor import Monitor
from app.core.config import settings

async def check_monitor(
    db: AsyncSession,
    monitor: Monitor,
) -> Check:
    start_time = time.perf_counter()

    status_code: int | None = None
    error: str | None = None

    try:
        async with httpx.AsyncClient(
            timeout=settings.CHECK_TIMEOUT,
            follow_redirects=True,
            trust_env=False,
        ) as client:
            response = await client.get(monitor.url)

        status_code = response.status_code
        is_success = 200 <= status_code < 400

    except httpx.HTTPError as exc:
        is_success = False
        error = str(exc)

    latency = time.perf_counter() - start_time

    check = Check(
        monitor_id=monitor.id,
        status_code=status_code,
        latency=latency,
        is_success=is_success,
        error=error,
    )

    db.add(check)
    await db.commit()
    await db.refresh(check)

    return check