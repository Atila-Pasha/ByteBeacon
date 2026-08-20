from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    description="Open-source API and uptime monitoring for developers",
    version=settings.APP_VERSION,
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}