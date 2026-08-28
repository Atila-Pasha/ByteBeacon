"""
Tests for the NotificationService.
"""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch, ANY

import pytest

from app.services.notification_service import NotificationService
from app.models.incident import Incident
from app.models.monitor import Monitor
from app.models.user import User
from app.models.notification import Notification


class FakeAsyncSession:


    def __init__(self):
        self.added_notifications = []
        self.committed = False

    async def execute(self, query):

        result = MagicMock()
        result.scalar_one_or_none = MagicMock(return_value=None)
        return result

    def add(self, obj):

        if isinstance(obj, Notification):
            self.added_notifications.append(obj)

    async def commit(self):

        self.committed = True


class TestNotificationService:


    @pytest.mark.asyncio
    async def test_send_to_telegram_only(self):

        telegram_provider = AsyncMock()
        email_provider = AsyncMock()
        service = NotificationService(
            telegram_provider=telegram_provider,
            email_provider=email_provider,
        )


        user = SimpleNamespace(
            id=1,
            telegram_chat_id=123456789,
            email=None,
        )
        monitor = SimpleNamespace(
            id=1,
            name="Test Monitor",
            url="https://example.com",
            user_id=1,
        )
        incident = SimpleNamespace(
            id=1,
            monitor_id=1,
            reason="HTTP 500",
            started_at=datetime.now(timezone.utc),
            resolved_at=None,
        )


        db = FakeAsyncSession()


        monitor_result = MagicMock()
        monitor_result.scalar_one_or_none = MagicMock(return_value=monitor)

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=user)

        existing_result = MagicMock()
        existing_result.scalar_one_or_none = MagicMock(return_value=None)

        async def mock_execute(query):
            if "monitors" in str(query):
                return monitor_result
            elif "users" in str(query):
                return user_result
            elif "notifications" in str(query):
                return existing_result
            return MagicMock()

        db.execute = mock_execute

        await service.send_incident_notification(db, incident, "down")


        telegram_provider.send.assert_called_once()
        email_provider.send.assert_not_called()
        assert len(db.added_notifications) == 1
        assert db.added_notifications[0].channel == "telegram"
        assert db.added_notifications[0].status == "sent"
        assert db.committed

    @pytest.mark.asyncio
    async def test_send_to_email_only(self):
        """Test sending notification via Email only."""
        # Setup
        telegram_provider = AsyncMock()
        email_provider = AsyncMock()
        service = NotificationService(
            telegram_provider=telegram_provider,
            email_provider=email_provider,
        )


        user = SimpleNamespace(
            id=1,
            telegram_chat_id=None,
            email="user@example.com",
        )
        monitor = SimpleNamespace(
            id=1,
            name="Test Monitor",
            url="https://example.com",
            user_id=1,
        )
        incident = SimpleNamespace(
            id=1,
            monitor_id=1,
            reason="HTTP 500",
            started_at=datetime.now(timezone.utc),
            resolved_at=None,
        )


        db = FakeAsyncSession()


        monitor_result = MagicMock()
        monitor_result.scalar_one_or_none = MagicMock(return_value=monitor)

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=user)

        existing_result = MagicMock()
        existing_result.scalar_one_or_none = MagicMock(return_value=None)


        async def mock_execute(query):
            if "monitors" in str(query):
                return monitor_result
            elif "users" in str(query):
                return user_result
            elif "notifications" in str(query):
                return existing_result
            return MagicMock()

        db.execute = mock_execute


        await service.send_incident_notification(db, incident, "down")


        telegram_provider.send.assert_not_called()
        email_provider.send.assert_called_once()
        assert len(db.added_notifications) == 1
        assert db.added_notifications[0].channel == "email"
        assert db.added_notifications[0].status == "sent"

    @pytest.mark.asyncio
    async def test_send_to_both_telegram_and_email(self):

        telegram_provider = AsyncMock()
        email_provider = AsyncMock()
        service = NotificationService(
            telegram_provider=telegram_provider,
            email_provider=email_provider,
        )


        user = SimpleNamespace(
            id=1,
            telegram_chat_id=123456789,
            email="user@example.com",
        )
        monitor = SimpleNamespace(
            id=1,
            name="Test Monitor",
            url="https://example.com",
            user_id=1,
        )
        incident = SimpleNamespace(
            id=1,
            monitor_id=1,
            reason="HTTP 500",
            started_at=datetime.now(timezone.utc),
            resolved_at=None,
        )


        db = FakeAsyncSession()


        monitor_result = MagicMock()
        monitor_result.scalar_one_or_none = MagicMock(return_value=monitor)

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=user)

        existing_result = MagicMock()
        existing_result.scalar_one_or_none = MagicMock(return_value=None)

        async def mock_execute(query):
            if "monitors" in str(query):
                return monitor_result
            elif "users" in str(query):
                return user_result
            elif "notifications" in str(query):
                return existing_result
            return MagicMock()

        db.execute = mock_execute

        await service.send_incident_notification(db, incident, "down")


        assert telegram_provider.send.call_count == 1
        assert email_provider.send.call_count == 1
        

        assert len(db.added_notifications) == 2
        channels = {n.channel for n in db.added_notifications}
        assert channels == {"telegram", "email"}

    @pytest.mark.asyncio
    async def test_telegram_provider_failure_recorded(self):

        telegram_provider = AsyncMock()
        telegram_provider.send.side_effect = Exception("Telegram API error")
        email_provider = AsyncMock()
        service = NotificationService(
            telegram_provider=telegram_provider,
            email_provider=email_provider,
        )


        user = SimpleNamespace(
            id=1,
            telegram_chat_id=123456789,
            email="user@example.com",
        )
        monitor = SimpleNamespace(
            id=1,
            name="Test Monitor",
            url="https://example.com",
            user_id=1,
        )
        incident = SimpleNamespace(
            id=1,
            monitor_id=1,
            reason="HTTP 500",
            started_at=datetime.now(timezone.utc),
            resolved_at=None,
        )

        db = FakeAsyncSession()


        monitor_result = MagicMock()
        monitor_result.scalar_one_or_none = MagicMock(return_value=monitor)

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=user)

        existing_result = MagicMock()
        existing_result.scalar_one_or_none = MagicMock(return_value=None)


        async def mock_execute(query):
            if "monitors" in str(query):
                return monitor_result
            elif "users" in str(query):
                return user_result
            elif "notifications" in str(query):
                return existing_result
            return MagicMock()

        db.execute = mock_execute

        await service.send_incident_notification(db, incident, "down")


        assert len(db.added_notifications) == 2
        

        telegram_notif = next(
            (n for n in db.added_notifications if n.channel == "telegram"), None
        )
        assert telegram_notif is not None
        assert telegram_notif.status == "failed"
        assert "Telegram API error" in telegram_notif.error


        email_notif = next(
            (n for n in db.added_notifications if n.channel == "email"), None
        )
        assert email_notif is not None
        assert email_notif.status == "sent"

    @pytest.mark.asyncio
    async def test_duplicate_notification_prevention(self):

        telegram_provider = AsyncMock()
        email_provider = AsyncMock()
        service = NotificationService(
            telegram_provider=telegram_provider,
            email_provider=email_provider,
        )


        user = SimpleNamespace(
            id=1,
            telegram_chat_id=123456789,
            email=None,
        )
        monitor = SimpleNamespace(
            id=1,
            name="Test Monitor",
            url="https://example.com",
            user_id=1,
        )
        incident = SimpleNamespace(
            id=1,
            monitor_id=1,
            reason="HTTP 500",
            started_at=datetime.now(timezone.utc),
            resolved_at=None,
        )

        existing_notification = SimpleNamespace(
            id=1,
            incident_id=1,
            channel="telegram",
            event_type="down",
        )


        db = FakeAsyncSession()


        monitor_result = MagicMock()
        monitor_result.scalar_one_or_none = MagicMock(return_value=monitor)

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=user)

        existing_result = MagicMock()
        existing_result.scalar_one_or_none = MagicMock(
            return_value=existing_notification
        )


        async def mock_execute(query):
            if "monitors" in str(query):
                return monitor_result
            elif "users" in str(query):
                return user_result
            elif "notifications" in str(query):
                return existing_result
            return MagicMock()

        db.execute = mock_execute


        await service.send_incident_notification(db, incident, "down")


        telegram_provider.send.assert_not_called()
        
        assert len(db.added_notifications) == 0

    @pytest.mark.asyncio
    async def test_recovery_event_generates_notification(self):

        telegram_provider = AsyncMock()
        email_provider = AsyncMock()
        service = NotificationService(
            telegram_provider=telegram_provider,
            email_provider=email_provider,
        )

        started_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        resolved_at = datetime(2024, 1, 1, 10, 30, 0, tzinfo=timezone.utc)

        user = SimpleNamespace(
            id=1,
            telegram_chat_id=123456789,
            email=None,
        )
        monitor = SimpleNamespace(
            id=1,
            name="Test Monitor",
            url="https://example.com",
            user_id=1,
        )
        incident = SimpleNamespace(
            id=1,
            monitor_id=1,
            reason="HTTP 500",
            started_at=started_at,
            resolved_at=resolved_at,
        )

        db = FakeAsyncSession()


        monitor_result = MagicMock()
        monitor_result.scalar_one_or_none = MagicMock(return_value=monitor)

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=user)

        existing_result = MagicMock()
        existing_result.scalar_one_or_none = MagicMock(return_value=None)


        async def mock_execute(query):
            if "monitors" in str(query):
                return monitor_result
            elif "users" in str(query):
                return user_result
            elif "notifications" in str(query):
                return existing_result
            return MagicMock()

        db.execute = mock_execute


        await service.send_incident_notification(db, incident, "recovery")


        telegram_provider.send.assert_called_once()
        
        call_kwargs = telegram_provider.send.call_args[1]
        sent_text = call_kwargs["text"]
        

        assert "🟢" in sent_text  
        assert "Monitor Recovered" in sent_text
        assert "30m" in sent_text 

    @pytest.mark.asyncio
    async def test_down_event_generates_notification(self):

        telegram_provider = AsyncMock()
        email_provider = AsyncMock()
        service = NotificationService(
            telegram_provider=telegram_provider,
            email_provider=email_provider,
        )

        user = SimpleNamespace(
            id=1,
            telegram_chat_id=123456789,
            email=None,
        )
        monitor = SimpleNamespace(
            id=1,
            name="Test Monitor",
            url="https://example.com",
            user_id=1,
        )
        incident = SimpleNamespace(
            id=1,
            monitor_id=1,
            reason="HTTP 503",
            started_at=datetime.now(timezone.utc),
            resolved_at=None,
        )


        db = FakeAsyncSession()

        monitor_result = MagicMock()
        monitor_result.scalar_one_or_none = MagicMock(return_value=monitor)

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=user)

        existing_result = MagicMock()
        existing_result.scalar_one_or_none = MagicMock(return_value=None)


        async def mock_execute(query):
            if "monitors" in str(query):
                return monitor_result
            elif "users" in str(query):
                return user_result
            elif "notifications" in str(query):
                return existing_result
            return MagicMock()

        db.execute = mock_execute

        await service.send_incident_notification(db, incident, "down")

        telegram_provider.send.assert_called_once()

        call_kwargs = telegram_provider.send.call_args[1]
        sent_text = call_kwargs["text"]

        assert "🔴" in sent_text 
        assert "Monitor Down" in sent_text
        assert "HTTP 503" in sent_text

    @pytest.mark.asyncio
    async def test_single_commit_for_multiple_notifications(self):
 
        telegram_provider = AsyncMock()
        email_provider = AsyncMock()
        service = NotificationService(
            telegram_provider=telegram_provider,
            email_provider=email_provider,
        )


        user = SimpleNamespace(
            id=1,
            telegram_chat_id=123456789,
            email="user@example.com",
        )
        monitor = SimpleNamespace(
            id=1,
            name="Test Monitor",
            url="https://example.com",
            user_id=1,
        )
        incident = SimpleNamespace(
            id=1,
            monitor_id=1,
            reason="HTTP 500",
            started_at=datetime.now(timezone.utc),
            resolved_at=None,
        )


        db = FakeAsyncSession()
        commit_count = 0

        original_commit = db.commit

        async def tracked_commit():
            nonlocal commit_count
            commit_count += 1
            await original_commit()

        db.commit = tracked_commit

        monitor_result = MagicMock()
        monitor_result.scalar_one_or_none = MagicMock(return_value=monitor)

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=user)

        existing_result = MagicMock()
        existing_result.scalar_one_or_none = MagicMock(return_value=None)

        async def mock_execute(query):
            if "monitors" in str(query):
                return monitor_result
            elif "users" in str(query):
                return user_result
            elif "notifications" in str(query):
                return existing_result
            return MagicMock()

        db.execute = mock_execute
        await service.send_incident_notification(db, incident, "down")


        assert commit_count == 1
        assert len(db.added_notifications) == 2

    @pytest.mark.asyncio
    async def test_invalid_event_type_skipped(self):

        telegram_provider = AsyncMock()
        email_provider = AsyncMock()
        service = NotificationService(
            telegram_provider=telegram_provider,
            email_provider=email_provider,
        )

        user = SimpleNamespace(
            id=1,
            telegram_chat_id=123456789,
            email=None,
        )
        monitor = SimpleNamespace(
            id=1,
            name="Test Monitor",
            url="https://example.com",
            user_id=1,
        )
        incident = SimpleNamespace(
            id=1,
            monitor_id=1,
            reason="HTTP 500",
            started_at=datetime.now(timezone.utc),
            resolved_at=None,
        )


        db = FakeAsyncSession()

        monitor_result = MagicMock()
        monitor_result.scalar_one_or_none = MagicMock(return_value=monitor)

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=user)


        async def mock_execute(query):
            if "monitors" in str(query):
                return monitor_result
            elif "users" in str(query):
                return user_result
            return MagicMock()

        db.execute = mock_execute


        await service.send_incident_notification(db, incident, "invalid_type")


        telegram_provider.send.assert_not_called()
        email_provider.send.assert_not_called()
        

        assert len(db.added_notifications) == 0
