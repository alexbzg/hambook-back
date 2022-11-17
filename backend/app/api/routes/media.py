from fastapi import Depends, APIRouter, HTTPException, Path, Body, status

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.models.media import MediaUpload, MediaInDB, MediaPublic, MediaType
from app.models.user import UserInDB
from app.models.core import FileType
from app.db.repositories.media import MediaRepository
from app.services.static_files import create_path, open_file, delete_file
from app.core.config import SRV_URI

router = APIRouter()

@router.put("/me/", response_model=MediaPublic, name="media:upload")
async def upload_media(
	media_upload: MediaUpload = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
	media_repo: MediaRepository = Depends(get_repository(MediaRepository)),    
) -> MediaPublic:
    
    file_ext = None
    if media_upload.file.content_type == 'image/jpeg':
        file_ext = 'jpeg'
    elif media_upload.file.content_type == 'image/png':
        file_ext = 'png'
    
    file_path = create_path(
            file_type=FileType.media, 
            media_type=media_upload.media_type, 
            ext=file_ext)

    async with open_file(file_path, 'wb') as out_file:
        while content := await in_file.read(1024):  
            await out_file.write(content)

    #if it is avatar upload remove existing
    if media_upload.media_type == MediaType.avatar:
        prev_avatar = await media_repo.get_media_by_user_id_media_type(
                user_id=current_user.id, media_type=MediaType.avatar)
        if prev_avatar:
            await media_repo.delete_media(id=prev_avatar[0].id)

    media_record = await media_repo.create_media(
        media_create=media_upload.copy(exclude={'file'}, update={'file_path': file_path}))


    return MediaPublic(**media_record.copy(exclude={'file_path'}, update={'url': f"{SRV_URI}{file_path}"}))



