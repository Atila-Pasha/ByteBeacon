from fastapi import APIRouter

from app.api.v1.monitors import router as monitor_router
from app.api.v1.users import router as user_router
from app.api.v1.auth import router as auth_router
from app.api.v1.checks import router as check_router
from app.api.v1.incidents import router as incident_router

router = APIRouter(
    prefix="/v1",
)

router.include_router(auth_router)
router.include_router(user_router)
router.include_router(monitor_router)
router.include_router(check_router)
router.include_router(incident_router)
