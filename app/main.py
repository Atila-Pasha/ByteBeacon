from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.session import engine

from app.api.v1.router import router as v1_router
from app.monitoring.scheduler import MonitorScheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = MonitorScheduler()
    scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()
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