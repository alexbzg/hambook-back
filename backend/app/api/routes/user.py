from fastapi import APIRouter, Body, Depends
from starlette.status import HTTP_201_CREATED

from app.models.user import UserCreate, UserInDB
from app.db.repositories.users import UsersRepository
from app.api.dependencies.database import get_repository


router = APIRouter()

@router.post("/", response_model=UserInDB, name="users:create-user", status_code=HTTP_201_CREATED)
async def create_new_cleaning(
    new_user: UserCreate = Body(..., embed=True),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    ) -> UserInDB:
    created_user = await users_repo.create_user(new_user=new_user)

    return created_user


