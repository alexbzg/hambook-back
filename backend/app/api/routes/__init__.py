from fastapi import APIRouter

from app.api.routes.test import router as test_router
from app.api.routes.users import router as users_router

router = APIRouter()

router.include_router(test_router, prefix="/test", tags=["test"])
router.include_router(users_router, prefix="/users", tags=["user"])

@router.get("/")
async def test() -> dict:
    return {'status': 'Ok', 'foo': 'bar'}

