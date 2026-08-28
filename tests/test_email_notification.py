
import smtplib
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from app.notifications.email import EmailNotificationProvider


class TestEmailNotificationProvider:


    @pytest.mark.asyncio
    async def test_send_email_with_tls(self):

        provider = EmailNotificationProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            smtp_from_email="test@gmail.com",
            smtp_from_name="Test",
            smtp_use_tls=True,
            smtp_use_ssl=False,
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=None)

            await provider.send(
                recipient="user@example.com",
                text="<b>Test</b> message",
            )


            mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
            

            mock_server.starttls.assert_called_once()
            

            mock_server.login.assert_called_once_with("test@gmail.com", "password")
            
  
            mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_ssl(self):

        provider = EmailNotificationProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=465,
            smtp_user="test@gmail.com",
            smtp_password="password",
            smtp_from_email="test@gmail.com",
            smtp_from_name="Test",
            smtp_use_tls=False,
            smtp_use_ssl=True,
        )

        with patch("smtplib.SMTP_SSL") as mock_smtp_ssl:
            mock_server = MagicMock()
            mock_smtp_ssl.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp_ssl.return_value.__exit__ = MagicMock(return_value=None)

            await provider.send(
                recipient="user@example.com",
                text="<b>Test</b> message",
            )


            mock_smtp_ssl.assert_called_once_with("smtp.gmail.com", 465)
            

            mock_server.starttls.assert_not_called()
            

            mock_server.login.assert_called_once_with("test@gmail.com", "password")
            

            mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_recipient_used(self):

        provider = EmailNotificationProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            smtp_from_email="test@gmail.com",
            smtp_from_name="Test",
            smtp_use_tls=True,
            smtp_use_ssl=False,
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=None)

            await provider.send(
                recipient="recipient@example.com",
                text="<b>Test</b>",
            )


            sent_msg = mock_server.send_message.call_args[0][0]
            

            assert sent_msg["To"] == "recipient@example.com"

    @pytest.mark.asyncio
    async def test_send_email_sender_used(self):

        provider = EmailNotificationProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            smtp_from_email="noreply@bytebeacon.com",
            smtp_from_name="ByteBeacon Alerts",
            smtp_use_tls=True,
            smtp_use_ssl=False,
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=None)

            await provider.send(
                recipient="user@example.com",
                text="<b>Test</b>",
            )

            sent_msg = mock_server.send_message.call_args[0][0]
            assert sent_msg["From"] == "ByteBeacon Alerts <noreply@bytebeacon.com>"

    @pytest.mark.asyncio
    async def test_send_email_html_content(self):

        provider = EmailNotificationProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            smtp_from_email="test@gmail.com",
            smtp_from_name="Test",
            smtp_use_tls=True,
            smtp_use_ssl=False,
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=None)

            html_content = "<b>🔴 Monitor Down</b><br>URL: http://example.com"
            await provider.send(
                recipient="user@example.com",
                text=html_content,
            )

            sent_msg = mock_server.send_message.call_args[0][0]


            assert sent_msg["Subject"] == "ByteBeacon Alert"
            assert sent_msg["To"] == "user@example.com"
            assert sent_msg.is_multipart()
            
   
            found_html = False
            for part in sent_msg.walk():
                if part.get_content_type() == "text/html":
                    found_html = True
                    break
            assert found_html

    @pytest.mark.asyncio
    async def test_send_email_missing_smtp_host(self):

        provider = EmailNotificationProvider(
            smtp_host="",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            smtp_from_email="test@gmail.com",
            smtp_from_name="Test",
        )

        with patch("smtplib.SMTP") as mock_smtp:
            await provider.send(
                recipient="user@example.com",
                text="<b>Test</b>",
            )
            

            mock_smtp.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_email_missing_from_email(self):

        provider = EmailNotificationProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            smtp_from_email="",
            smtp_from_name="Test",
        )

        with patch("smtplib.SMTP") as mock_smtp:
            await provider.send(
                recipient="user@example.com",
                text="<b>Test</b>",
            )
            

            mock_smtp.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_email_missing_credentials(self):

        provider = EmailNotificationProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="",
            smtp_password="",
            smtp_from_email="test@gmail.com",
            smtp_from_name="Test",
        )

        with patch("smtplib.SMTP") as mock_smtp:
            await provider.send(
                recipient="user@example.com",
                text="<b>Test</b>",
            )
            

            mock_smtp.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_email_missing_password_only(self):

        provider = EmailNotificationProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="",
            smtp_from_email="test@gmail.com",
            smtp_from_name="Test",
        )

        with patch("smtplib.SMTP") as mock_smtp:
            await provider.send(
                recipient="user@example.com",
                text="<b>Test</b>",
            )
            

            mock_smtp.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_email_authentication_error(self):

        provider = EmailNotificationProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="wrong_password",
            smtp_from_email="test@gmail.com",
            smtp_from_name="Test",
            smtp_use_tls=True,
            smtp_use_ssl=False,
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=None)

            # Simulate authentication error
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
                535, "Invalid credentials"
            )

            with pytest.raises(smtplib.SMTPAuthenticationError):
                await provider.send(
                    recipient="user@example.com",
                    text="<b>Test</b>",
                )

    @pytest.mark.asyncio
    async def test_send_email_smtp_error(self):

        provider = EmailNotificationProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            smtp_from_email="test@gmail.com",
            smtp_from_name="Test",
            smtp_use_tls=True,
            smtp_use_ssl=False,
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=None)
            

            mock_server.send_message.side_effect = smtplib.SMTPException(
                "Connection lost"
            )

            with pytest.raises(smtplib.SMTPException):
                await provider.send(
                    recipient="user@example.com",
                    text="<b>Test</b>",
                )

    @pytest.mark.asyncio
    async def test_send_email_connection_closed_on_error(self):

        provider = EmailNotificationProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            smtp_from_email="test@gmail.com",
            smtp_from_name="Test",
            smtp_use_tls=True,
            smtp_use_ssl=False,
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_server)
            mock_context.__exit__ = MagicMock(return_value=None)
            mock_smtp.return_value = mock_context
            
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
                535, "Invalid credentials"
            )

            with pytest.raises(smtplib.SMTPAuthenticationError):
                await provider.send(
                    recipient="user@example.com",
                    text="<b>Test</b>",
                )


            mock_context.__exit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_default_settings(self):
        """Test sending email with default settings from environment."""
        with patch("app.notifications.email.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.gmail.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = "user@gmail.com"
            mock_settings.SMTP_PASSWORD = "pass"
            mock_settings.SMTP_FROM_EMAIL = "from@gmail.com"
            mock_settings.SMTP_FROM_NAME = "From Name"
            mock_settings.SMTP_USE_TLS = True
            mock_settings.SMTP_USE_SSL = False

            provider = EmailNotificationProvider()

            assert provider.smtp_host == "smtp.gmail.com"
            assert provider.smtp_port == 587
            assert provider.smtp_user == "user@gmail.com"
            assert provider.smtp_password == "pass"
            assert provider.smtp_from_email == "from@gmail.com"
            assert provider.smtp_from_name == "From Name"
            assert provider.smtp_use_tls is True
            assert provider.smtp_use_ssl is False
