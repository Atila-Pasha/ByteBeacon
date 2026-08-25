import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.models.monitor import Monitor
from app.models.notification import Notification
from app.models.user import User
from app.notifications.base import NotificationProvider
from app.notifications.telegram import TelegramNotificationProvider

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, provider: NotificationProvider | None = None) -> None:
        self.provider = provider or TelegramNotificationProvider()

    async def send_incident_notification(
        self,
        db: AsyncSession,
        incident: Incident,
        event_type: str,
    ) -> None:
        if incident.monitor_id is None:
            return

        monitor_result = await db.execute(
            select(Monitor).where(Monitor.id == incident.monitor_id)
        )
        monitor = monitor_result.scalar_one_or_none()
        if monitor is None:
            return

        user_result = await db.execute(select(User).where(User.id == monitor.user_id))
        user = user_result.scalar_one_or_none()
        if user is None or user.telegram_chat_id is None:
            return

        if event_type == "down":
            text = (
                "<b>🔴 Monitor Down</b>\n\n"
                f"Monitor: {monitor.name}\n"
                f"URL: {monitor.url}\n"
                f"Reason: {incident.reason or 'Unknown'}\n"
                f"Time: {datetime.now(timezone.utc).strftime('%H:%M UTC')}"
            )
        elif event_type == "recovery":
            if incident.resolved_at is not None and incident.started_at is not None:
                delta = incident.resolved_at - incident.started_at
                total_minutes = int(delta.total_seconds() // 60)
                hours = total_minutes // 60
                minutes = total_minutes % 60
                duration_text = f"{hours}h {minutes}m" if hours else f"{minutes}m"
            else:
                duration_text = "unknown"
            text = (
                "<b>🟢 Monitor Recovered</b>\n\n"
                f"Monitor: {monitor.name}\n"
                f"URL: {monitor.url}\n"
                f"Recovered: {datetime.now(timezone.utc).strftime('%H:%M UTC')}\n"
                f"Duration: {duration_text}"
            )
        else:
            return

        existing = await db.execute(
            select(Notification).where(
                Notification.incident_id == incident.id,
                Notification.channel == "telegram",
                Notification.event_type == event_type,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return

        try:
            await self.provider.send(chat_id=user.telegram_chat_id, text=text)
            status = "sent"
            error = None
        except Exception as exc:
            logger.exception("Telegram notification delivery failed")
            status = "failed"
            error = str(exc)

        notification = Notification(
            incident_id=incident.id,
            user_id=user.id,
            channel="telegram",
            provider="telegram",
            event_type=event_type,
            status=status,
            error=error,
            sent_at=datetime.now(timezone.utc),
        )
        db.add(notification)
        await db.commit()


notification_service = NotificationService()
