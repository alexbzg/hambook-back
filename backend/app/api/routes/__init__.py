from fastapi import APIRouter

from app.api.routes.users import router as users_router
from app.api.routes.profiles import router as profiles_router

router = APIRouter()

router.include_router(users_router, prefix="/users", tags=["user"])
router.include_router(profiles_router, prefix="/profiles", tags=["profile"])

@router.get("/")
async def test() -> dict:
    return {'status': 'Ok'}

