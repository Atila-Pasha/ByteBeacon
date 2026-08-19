from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    description="Open-source API and uptime monitoring for developers",
    version=settings.app_version,
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}