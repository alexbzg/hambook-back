from fastapi import Depends, HTTPException, status

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_optional_user, get_current_active_user
from app.db.repositories.posts import PostsRepository
from app.models.post import PostInDB, PostVisibility
from app.models.user import UserInDB


async def get_post_for_update(post_id: int, 
	current_user: UserInDB = Depends(get_current_active_user),
    posts_repo: PostsRepository = Depends(get_repository(PostsRepository))) -> PostInDB:

    post = await posts_repo.get_post_id(id=post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if int(post.user_id) != int(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    return post

async def get_visibility_level(author_id: int, 
	current_user: UserInDB = Depends(get_current_optional_user)) -> PostVisibility:

    if not current_user:
        return PostVisibility.everybody

    if current_user.is_admin or int(current_usr.id) == author_id:
        return PostVisibility.private

    return PostVisibility.logged_users

async def get_post_for_view(post_id: int, 
	current_user: UserInDB = Depends(get_current_optional_user),
    posts_repo: PostsRepository = Depends(get_repository(PostsRepository))) -> PostInDB:

    post = await posts_repo.get_post_id(id=post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if get_visibility_level(post.user_id) > post.visibility:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    return post



