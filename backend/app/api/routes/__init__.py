from fastapi import APIRouter

from app.api.routes.users import router as users_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.media import router as media_router
from app.api.routes.qso_logs import router as qso_logs_router


router = APIRouter()

router.include_router(users_router, prefix="/users", tags=["user"])
router.include_router(profiles_router, prefix="/profiles", tags=["profile"])
router.include_router(media_router, prefix="/media", tags=["media"])
router.include_router(qso_logs_router, prefix="/qso/logs", tags=["qso-logs"])


@router.get("/")
async def test() -> dict:
    return {'status': 'Ok'}

