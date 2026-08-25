import asyncio
import ipaddress
import socket
import time
from urllib.parse import urlsplit

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.check import Check
from app.models.monitor import Monitor
from app.core.config import settings
from app.services.incident_service import reconcile_incident_for_check
from app.services.notification_service import notification_service


class UnsafeMonitorTargetError(ValueError):
    """Raised when a monitor URL resolves to a non-public network address."""


async def validate_monitor_target(url: str) -> None:
    """Reject targets that could expose services on the worker's private network."""
    parsed_url = urlsplit(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
        raise UnsafeMonitorTargetError("Monitor URL must use HTTP or HTTPS")

    try:
        addresses = await asyncio.get_running_loop().getaddrinfo(
            parsed_url.hostname,
            parsed_url.port or (443 if parsed_url.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise UnsafeMonitorTargetError("Monitor host could not be resolved") from exc

    resolved_ips = {address[4][0] for address in addresses}
    if not resolved_ips or any(not ipaddress.ip_address(ip).is_global for ip in resolved_ips):
        raise UnsafeMonitorTargetError("Monitor target must resolve only to public IP addresses")


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
            follow_redirects=False,
            trust_env=False,
        ) as client:
            url = monitor.url
            for _ in range(6):
                await validate_monitor_target(url)
                response = await client.get(url)

                if not response.is_redirect:
                    break

                location = response.headers.get("location")
                if location is None:
                    break
                url = str(response.url.join(location))
            else:
                raise httpx.TooManyRedirects("Exceeded maximum redirects")

        status_code = response.status_code
        is_success = 200 <= status_code < 400

    except (httpx.HTTPError, UnsafeMonitorTargetError) as exc:
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
    incident = await reconcile_incident_for_check(db, check)
    await db.commit()
    await db.refresh(check)

    if incident is not None:
        try:
            if check.is_success:
                await notification_service.send_incident_notification(db, incident, "recovery")
            else:
                await notification_service.send_incident_notification(db, incident, "down")
        except Exception:
            pass

    return check
