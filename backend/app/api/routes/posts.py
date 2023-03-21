from typing import List, Optional
import json

from fastapi import Depends, APIRouter, HTTPException, Path, Body, Form, status, UploadFile, File
from starlette.status import (
        HTTP_400_BAD_REQUEST, 
        HTTP_401_UNAUTHORIZED, 
        HTTP_404_NOT_FOUND )
from app.api.dependencies.auth import get_current_active_user, get_current_optional_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.posts import get_post_for_update, get_post_for_view, get_visibility_level
from app.models.post import PostBase, PostInDB, PostPublic, PostVisibility, PostType
from app.models.user import UserInDB
from app.db.repositories.posts import PostsRepository

router = APIRouter()

@router.post("/", response_model=PostPublic, name="posts:create-post")
async def create_post(*,
    new_post: PostBase = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
	posts_repo: PostsRepository = Depends(get_repository(PostsRepository)),    
) -> PostPublic:

    if not current_user.is_admin and new_post.post_type == PostType.site:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    created_post = await posts_repo.create_post(new_post=new_post, requesting_user=current_user)

    return PostPublic(**created_post.dict())

@router.delete("/{post_id}", response_model=dict, name="posts:delete-post")
async def delete_post(*,
    post_id: int,
	current_user: UserInDB = Depends(get_current_active_user),
	posts_repo: PostsRepository = Depends(get_repository(PostsRepository)),    
    post: PostInDB = Depends(get_post_for_update)
) -> dict:

    await posts_repo.delete_post(id=post_id)

    return {"result": "Ok"}

@router.put("/{post_id}", response_model=PostPublic, name="posts:update-post")
async def update_post(*,
    post_update: PostBase = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
	posts_repo: PostsRepository = Depends(get_repository(PostsRepository)),    
    post: PostInDB = Depends(get_post_for_update)
) -> PostPublic:

    updated_post = await posts_repo.update_post(post=post, post_update=post_update)

    return PostPublic(**updated_post.dict())

@router.get("/", response_model=List[PostPublic], name="posts:query-by-user")
async def posts_query_by_user(*,
    user_id: int,
	current_user: Optional[UserInDB] = Depends(get_current_optional_user),
    visibility: PostVisibility = Depends(get_visibility_level),
	posts_repo: PostsRepository = Depends(get_repository(PostsRepository)),    
) -> List[PostPublic]:

    posts = await posts_repo.get_posts_by_user_id(user_id=user_id, visibility=visibility)

    if not posts:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Posts not found"
        )

    return [PostPublic(**post.dict()) for post in posts]

@router.get("/{post_id}", response_model=PostPublic, name="posts:query-by-post-id")
async def post_by_id(*,
    post_id: int,
	current_user: Optional[UserInDB] = Depends(get_current_optional_user),
    post: PostInDB = Depends(get_post_for_view)
) -> PostPublic:

    return PostPublic(**post.dict())


