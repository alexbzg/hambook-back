
from fastapi import Depends, APIRouter, HTTPException, Path, Body, Form, status, UploadFile, File
from starlette.status import HTTP_201_CREATED
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.models.friend import FriendBase, FriendInDB, FriendPublic
from app.models.user import UserInDB
from app.db.repositories.friends import FriendsRepository

router = APIRouter()

@router.post("/{friend_id}", response_model=FriendPublic, name="friend:add",  status_code=HTTP_201_CREATED)
async def add_friend(*,
    friend_id: int,
	current_user: UserInDB = Depends(get_current_active_user),
	friends_repo: FriendsRepository = Depends(get_repository(FriendsRepository)),    
) -> FriendPublic:

    added_friend = await friends_repo.add_friend(requesting_user=current_user, friend_id=friend_id)

    return FriendPublic(**added_friend.dict())

@router.delete("/{friend_id}", response_model=dict, name="friend:delete")
async def delete_media(*,
    friend_id: int,
	current_user: UserInDB = Depends(get_current_active_user),
	friends_repo: FriendsRepository = Depends(get_repository(FriendsRepository)),    
) -> dict:

    await friends_repo.delete_friend(requesting_user=current_user, friend_id=friend_id)

    return {"result": "Ok"}
