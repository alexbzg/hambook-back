from typing import List

from fastapi import Depends, APIRouter, HTTPException, Path, Body, Form, status, UploadFile, File
from pydantic import ValidationError
from starlette.status import (
        HTTP_400_BAD_REQUEST, 
        HTTP_401_UNAUTHORIZED, 
        HTTP_404_NOT_FOUND )
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.models.media import MediaUpload, MediaInDB, MediaPublic, MediaType
from app.models.user import UserInDB
from app.db.repositories.media import MediaRepository, mediaPublicFromDB
from app.services.static_files import get_url_by_path

import logging

router = APIRouter()

@router.post("/", response_model=MediaPublic, name="media:upload")
async def upload_media(*,
    media_type: MediaType = Form(...),
    file: UploadFile = File(...),
	current_user: UserInDB = Depends(get_current_active_user),
	media_repo: MediaRepository = Depends(get_repository(MediaRepository)),    
) -> MediaPublic:

    try:
        media_upload = MediaUpload(user_id=current_user.id, media_type=media_type, file=file)
    except ValidationError:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid file type"
        )

    created_media = await media_repo.upload_media(media_upload=media_upload)

    return MediaPublic(**created_media.copy(
        exclude={'file_path'},
        update={'url': get_url_by_path(created_media.file_path)}).dict())

@router.delete("/", response_model=dict, name="media:delete")
async def delete_media(*,
    media_id: int,
	current_user: UserInDB = Depends(get_current_active_user),
	media_repo: MediaRepository = Depends(get_repository(MediaRepository)),    
) -> dict:

    media_record = await media_repo.get_media_by_id(id=media_id)

    if not media_record:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    if int(media_record.user_id) != int(current_user.id):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    await media_repo.delete_media(id=media_id)

    return {"result": "Ok"}

@router.get("/{user_id}/{media_type}", response_model=List[MediaPublic], name="media:query-by-user-and-type")
async def media_query(*,
    user_id: int,
    media_type: MediaType,
	media_repo: MediaRepository = Depends(get_repository(MediaRepository)),    
) -> List[MediaPublic]:

    media_records = await media_repo.get_media_by_user_id_media_type(user_id=user_id, media_type=media_type)

    if not media_records:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Media not found"
        )

    return [mediaPublicFromDB(media) for media in media_records]

