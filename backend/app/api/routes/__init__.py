from fastapi import APIRouter

from app.api.routes.users import router as users_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.media import router as media_router
from app.api.routes.qso_logs import router as qso_logs_router
from app.api.routes.qso import router as qso_router
from app.api.routes.callsigns import router as callsigns_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.posts import router as posts_router
from app.api.routes.friends import router as friends_router

from app.api.routes.test import router as test_router

router = APIRouter()

router.include_router(users_router, prefix="/users", tags=["user"])
router.include_router(profiles_router, prefix="/profiles", tags=["profile"])
router.include_router(media_router, prefix="/media", tags=["media"])
router.include_router(qso_logs_router, prefix="/qso/logs", tags=["qso-logs"])
router.include_router(qso_router, prefix="/qso", tags=["qso"])
router.include_router(callsigns_router, prefix="/callsigns", tags=["callsigns"])
router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
router.include_router(posts_router, prefix="/posts", tags=["posts"])
router.include_router(friends_router, prefix="/friends", tags=["friends"])

router.include_router(test_router, prefix="/test", tags=["test"])

