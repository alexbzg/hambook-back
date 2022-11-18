from fastapi import Depends, APIRouter, HTTPException, Path, Body, Form, status, UploadFile, File
from pydantic import ValidationError
from starlette.status import HTTP_400_BAD_REQUEST

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.models.media import MediaUpload, MediaInDB, MediaPublic, MediaType
from app.models.user import UserInDB
from app.db.repositories.media import MediaRepository
from app.services.static_files import get_url_by_path

router = APIRouter()

@router.post("/", response_model=MediaPublic, name="media:upload")
async def upload_media(
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

