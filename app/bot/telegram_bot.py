import asyncio
import logging
from typing import Any

import httpx
from fastapi import FastAPI
from sqlalchemy import select

try:
    from telegram import Update
    from telegram.error import NetworkError
    from telegram.request import HTTPXRequest
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:  # pragma: no cover - depends on optional runtime library
    Update = Any  # type: ignore[assignment]
    NetworkError = Exception  # type: ignore[misc,assignment]
    HTTPXRequest = None  # type: ignore[assignment]
    Application = None  # type: ignore[assignment]
    CommandHandler = None  # type: ignore[assignment]
    ContextTypes = Any  # type: ignore[assignment]

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.services.telegram_service import TelegramConnectionError

logger = logging.getLogger(__name__)


class TelegramBotService:
    def __init__(self, app: FastAPI | None = None) -> None:
        self.app = app
        self.application: Application | None = None
        self.task: asyncio.Task[None] | None = None
        self._initialized = False
        self._running = False
        self._polling = False

    async def start(self) -> None:
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.info("Telegram bot is disabled because no token is configured")
            return

        if Application is None or CommandHandler is None or HTTPXRequest is None:
            logger.warning("python-telegram-bot is not installed; skipping Telegram bot startup")
            return

        if self.application is not None:
            return

        request_kwargs: dict[str, object] = {"trust_env": False}
        if settings.TELEGRAM_PROXY_URL:
            request_kwargs["proxy"] = settings.TELEGRAM_PROXY_URL

        telegram_request = HTTPXRequest(httpx_kwargs=request_kwargs)
        get_updates_request = HTTPXRequest(httpx_kwargs=request_kwargs)
        self.application = (
            Application.builder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .request(telegram_request)
            .get_updates_request(get_updates_request)
            .build()
        )
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CommandHandler("status", self.handle_status))
        self.application.add_handler(CommandHandler("disconnect", self.handle_disconnect))

        try:
            await self.application.initialize()
            self._initialized = True
            await self.application.start()
            self._running = True
            await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            self._polling = True
            logger.info("Telegram bot polling started")
        except NetworkError as error:
            logger.warning(
                "Telegram bot is unavailable; continuing without Telegram polling: %s",
                error,
            )
            await self.stop()
        except Exception:
            # A Telegram outage or blocked network must not prevent the API from
            # starting. ``stop`` only invokes lifecycle operations that completed.
            logger.exception("Telegram bot startup failed; continuing without Telegram polling")
            await self.stop()

    async def stop(self) -> None:
        if self.application is None:
            return

        if self.application.updater is not None and self._polling:
            await self.application.updater.stop()
            self._polling = False
        if self._running:
            await self.application.stop()
            self._running = False
        if self._initialized:
            await self.application.shutdown()
            self._initialized = False
        self.application = None

        if self.task is not None:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

    async def _connect_via_api(self, token: str, telegram_chat_id: int) -> None:
        api_base_url = settings.TELEGRAM_API_BASE_URL.rstrip("/")
        async with httpx.AsyncClient(
            timeout=settings.TELEGRAM_API_TIMEOUT,
            trust_env=False,
        ) as client:
            response = await client.post(
                f"{api_base_url}/v1/telegram/connect",
                json={
                    "token": token,
                    "telegram_chat_id": telegram_chat_id,
                },
            )
            if response.status_code >= 400:
                raise TelegramConnectionError("Connection failed")

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_chat or not update.effective_user:
            return

        args = context.args or []
        if not args:
            await update.effective_chat.send_message(
                "Generate a Telegram connection link from your ByteBeacon profile, then open it to connect this chat."
            )
            return

        telegram_chat_id = update.effective_chat.id
        token = args[0]

        try:
            await self._connect_via_api(token, telegram_chat_id)
            await update.effective_chat.send_message(
                "Telegram connected successfully to your ByteBeacon account."
            )
        except TelegramConnectionError:
            await update.effective_chat.send_message(
                "This Telegram connection link is invalid, expired, or already used. Please generate a new token in ByteBeacon."
            )
        except Exception:
            logger.exception("Unable to link Telegram chat")
            await update.effective_chat.send_message(
                "Telegram connection failed. Please try again in a moment."
            )

    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_chat:
            return

        chat_id = update.effective_chat.id
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).where(User.telegram_chat_id == chat_id))
                user = result.scalar_one_or_none()
        except Exception:
            logger.exception("Failed to load Telegram status")
            user = None

        if user is not None:
            await update.effective_chat.send_message("Your Telegram chat is connected to ByteBeacon.")
            return

        await update.effective_chat.send_message(
            "Your Telegram chat is not connected to a ByteBeacon account yet. Generate a connection link from your ByteBeacon profile and open it."
        )

    async def handle_disconnect(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_chat:
            return

        chat_id = update.effective_chat.id
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).where(User.telegram_chat_id == chat_id))
                user = result.scalar_one_or_none()
                if user is not None:
                    user.telegram_chat_id = None
                    await db.commit()
                    await update.effective_chat.send_message("Telegram disconnected from your ByteBeacon account.")
                    return
            await update.effective_chat.send_message("This Telegram chat is not connected to a ByteBeacon account.")
        except Exception:
            logger.exception("Failed to disconnect Telegram chat")
            await update.effective_chat.send_message("Unable to disconnect Telegram right now.")


telegram_bot_service = TelegramBotService()
