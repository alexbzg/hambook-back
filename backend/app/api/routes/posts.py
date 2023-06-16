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
from app.api.dependencies.media import get_media_for_update
from app.models.post import PostBase, PostUpdate, PostInDB, PostPublic, PostVisibility, PostType
from app.models.user import UserInDB
from app.db.repositories.posts import PostsRepository
from app.db.repositories.media import MediaRepository

router = APIRouter()

async def update_post_images(*,
    post_update: PostUpdate,
    post_id: int,
    current_user: UserInDB,
    media_repo: MediaRepository) -> None:

    for media_id in post_update.post_images:
        media = await get_media_for_update(media_id, current_user, media_repo)
        await media_repo.set_media_post_id(media_id=media.id, post_id=post_id)

    for media_id in post_update.deleted_images:
        media = await get_media_for_update(media_id, current_user, media_repo)
        await media_repo.delete_media(id=media.id)

@router.post("/", response_model=PostPublic, name="posts:create-post")
async def create_post(*,
    new_post: PostUpdate = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
	posts_repo: PostsRepository = Depends(get_repository(PostsRepository)),    
    media_repo: MediaRepository = Depends(get_repository(MediaRepository)),
) -> PostPublic:

    if not current_user.is_admin and new_post.post_type == PostType.site:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    created_post = await posts_repo.create_post(new_post=new_post, requesting_user=current_user)
    await update_post_images(post_update=new_post, post_id=created_post.id, 
            current_user=current_user, media_repo=media_repo)

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
    post_update: PostUpdate = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
	posts_repo: PostsRepository = Depends(get_repository(PostsRepository)),    
    media_repo: MediaRepository = Depends(get_repository(MediaRepository)),
    post: PostInDB = Depends(get_post_for_update)
) -> PostPublic:

    updated_post = await posts_repo.update_post(post=post, post_update=post_update)
    await update_post_images(post_update=post_update, post_id=post.id, 
            current_user=current_user, media_repo=media_repo)

    return PostPublic(**updated_post.dict())

@router.get("/", response_model=List[PostPublic], name="posts:query-by-user")
async def posts_query_by_user(*,
    user_id: int,
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

@router.get("/world", response_model=List[PostPublic], name="posts:site")
async def posts_site(*,
    visibility: PostVisibility = Depends(get_visibility_level),
	posts_repo: PostsRepository = Depends(get_repository(PostsRepository)),    
) -> List[PostPublic]:

    posts = await posts_repo.get_site_posts(visibility=visibility)

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


