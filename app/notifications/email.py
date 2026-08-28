import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.notifications.base import NotificationProvider

logger = logging.getLogger(__name__)


class EmailNotificationProvider(NotificationProvider):
    def __init__(
        self,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        smtp_from_email: str | None = None,
        smtp_from_name: str | None = None,
        smtp_use_tls: bool | None = None,
        smtp_use_ssl: bool | None = None,
    ) -> None:
        self.smtp_host = smtp_host or settings.SMTP_HOST
        self.smtp_port = smtp_port or settings.SMTP_PORT
        self.smtp_user = smtp_user or settings.SMTP_USER
        self.smtp_password = smtp_password or settings.SMTP_PASSWORD
        self.smtp_from_email = smtp_from_email or settings.SMTP_FROM_EMAIL
        self.smtp_from_name = smtp_from_name or settings.SMTP_FROM_NAME
        self.smtp_use_tls = (
            smtp_use_tls if smtp_use_tls is not None else settings.SMTP_USE_TLS
        )
        self.smtp_use_ssl = (
            smtp_use_ssl if smtp_use_ssl is not None else settings.SMTP_USE_SSL
        )

    async def send(self, *, recipient: str, text: str) -> None:

        if not self.smtp_host:
            logger.warning("SMTP host is not configured; skipping email notification")
            return

        if not self.smtp_from_email:
            logger.warning("SMTP from email is not configured; skipping email notification")
            return

        if not self.smtp_user or not self.smtp_password:
            logger.warning(
                "SMTP credentials are not configured; skipping email notification"
            )
            return

        try:
            self._send_email(
                to_email=recipient,
                subject="ByteBeacon Alert",
                html_content=text,
            )
        except smtplib.SMTPException:
            logger.exception("Email notification delivery failed")
            raise
        except Exception:
            logger.exception("Unexpected error sending email notification")
            raise

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> None:

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.smtp_from_name} <{self.smtp_from_email}>"
        msg["To"] = to_email


        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)


        try:
            if self.smtp_use_ssl:

                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:

                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if self.smtp_use_tls:
                        server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed; check credentials")
            raise
        except smtplib.SMTPException:
            logger.error("SMTP error occurred")
            raise
