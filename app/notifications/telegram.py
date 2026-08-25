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

    async def send(self, *, chat_id: int, text: str) -> None:
        if not self.api_token:
            logger.warning("Telegram bot token is not configured; skipping notification")
            return

        try:
            response = await self.client.post(
                f"/bot{self.api_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception("Telegram notification delivery failed")
            raise

    async def close(self) -> None:
        if self.client is not None and not self.client.is_closed:
            await self.client.aclose()
