from fastapi import Depends, HTTPException, status

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user
from app.db.repositories.media import MediaRepository
from app.models.media import MediaInDB
from app.models.user import UserInDB


async def get_media_for_update(media_id: int, 
	current_user: UserInDB = Depends(get_current_active_user),
    media_repo: MediaRepository = Depends(get_repository(MediaRepository))) -> MediaInDB:

    media = await media_repo.get_media_by_id(id=media_id)

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    if int(media.user_id) != int(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    return media

