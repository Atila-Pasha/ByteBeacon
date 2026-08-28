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
from app.notifications.email import EmailNotificationProvider

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        telegram_provider: NotificationProvider | None = None,
        email_provider: NotificationProvider | None = None,
    ) -> None:
        self.telegram_provider = telegram_provider or TelegramNotificationProvider()
        self.email_provider = email_provider or EmailNotificationProvider()

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
        if user is None:
            return


        text_html = self._generate_notification_text(incident, monitor, event_type)
        if text_html is None:
            return

        if user.telegram_chat_id is not None:
            await self._send_notification(
                db=db,
                incident=incident,
                user=user,
                channel="telegram",
                provider="telegram",
                event_type=event_type,
                text=text_html,
                recipient=str(user.telegram_chat_id),
                commit=False,
            )

        if user.email is not None:
            await self._send_notification(
                db=db,
                incident=incident,
                user=user,
                channel="email",
                provider="smtp",
                event_type=event_type,
                text=text_html,
                recipient=user.email,
                commit=False,
            )


        await db.commit()

    def _generate_notification_text(
        self,
        incident: Incident,
        monitor: Monitor,
        event_type: str,
    ) -> str | None:

        if event_type == "down":
            text = (
                "<b>🔴 Monitor Down</b><br><br>"
                f"Monitor: {monitor.name}<br>"
                f"URL: {monitor.url}<br>"
                f"Reason: {incident.reason or 'Unknown'}<br>"
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
                "<b>🟢 Monitor Recovered</b><br><br>"
                f"Monitor: {monitor.name}<br>"
                f"URL: {monitor.url}<br>"
                f"Recovered: {datetime.now(timezone.utc).strftime('%H:%M UTC')}<br>"
                f"Duration: {duration_text}"
            )
        else:
            return None

        return text

    async def _send_notification(
        self,
        db: AsyncSession,
        incident: Incident,
        user: "User",
        channel: str,
        provider: str,
        event_type: str,
        text: str,
        recipient: str,
        commit: bool = True,
    ) -> None:

        existing = await db.execute(
            select(Notification).where(
                Notification.incident_id == incident.id,
                Notification.channel == channel,
                Notification.event_type == event_type,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return


        notification_provider = (
            self.telegram_provider if channel == "telegram" else self.email_provider
        )

        try:
            await notification_provider.send(recipient=recipient, text=text)
            status = "sent"
            error = None
        except Exception as exc:
            logger.exception(f"{channel.upper()} notification delivery failed")
            status = "failed"
            error = str(exc)


        notification = Notification(
            incident_id=incident.id,
            user_id=user.id,
            channel=channel,
            provider=provider,
            event_type=event_type,
            status=status,
            error=error,
            sent_at=datetime.now(timezone.utc),
        )
        db.add(notification)
        
        if commit:
            await db.commit()


notification_service = NotificationService()
