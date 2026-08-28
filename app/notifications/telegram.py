import logging

import httpx

from app.core.config import settings
from app.notifications.base import NotificationProvider

logger = logging.getLogger(__name__)


class TelegramNotificationProvider(NotificationProvider):
    def __init__(self, api_token: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.api_token = api_token or settings.TELEGRAM_BOT_TOKEN
        self.client = client or httpx.AsyncClient(
            timeout=settings.TELEGRAM_API_TIMEOUT,
            base_url="https://api.telegram.org",
            trust_env=False,
            proxy=settings.TELEGRAM_PROXY_URL or None,
        )

    async def send(self, *, recipient: str, text: str) -> None:
        if not self.api_token:
            logger.warning("Telegram bot token is not configured; skipping notification")
            return

        try:
            chat_id = int(recipient)
        except (ValueError, TypeError):
            logger.error(f"Invalid Telegram chat_id: {recipient}")
            raise

        try:

            logger.debug(
                f"Sending Telegram notification to chat_id: {chat_id}, "
                f"text length: {len(text)}"
            )

            response = await self.client.post(
                f"/bot{self.api_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )


            logger.debug(f"Telegram API response status: {response.status_code}")

   
            if response.status_code >= 400:
                logger.error(
                    f"Telegram API error {response.status_code}: {response.text}"
                )

            response.raise_for_status()
            logger.debug("Telegram notification sent successfully")

        except httpx.HTTPError as e:
            logger.exception(f"Telegram notification delivery failed: {e}")
            raise

    async def close(self) -> None:
        if self.client is not None and not self.client.is_closed:
            await self.client.aclose()
