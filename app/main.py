from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.bot.telegram_bot import telegram_bot_service
from app.core.config import settings
from app.db.session import engine
from app.monitoring.scheduler import MonitorScheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = MonitorScheduler()
    if settings.SCHEDULER_ENABLED:
        scheduler.start()
        print("Scheduler started")

    try:
        await telegram_bot_service.start()
        print("Telegram bot service started")
        yield
    finally:
        if settings.SCHEDULER_ENABLED:
            await scheduler.stop()
        await telegram_bot_service.stop()
        await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    description="Open-source API and uptime monitoring for developers",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(v1_router)
