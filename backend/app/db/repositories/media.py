from typing import List
import logging
from PIL import Image

from app.db.repositories.base import BaseRepository
from app.models.media import MediaUpload, MediaInDB, MediaPublic, MediaType
from app.models.user import UserInDB
from app.models.core import FileType
from app.services.static_files import save_file, delete_file, get_url_by_path, full_path

CREATE_MEDIA_QUERY = """
    INSERT INTO media (media_type, file_path, user_id)
    VALUES (:media_type, :file_path, :user_id)
    RETURNING id, media_type, file_path, user_id;
"""

DELETE_MEDIA_QUERY = """
    DELETE from media 
    WHERE id = :id;
"""

GET_MEDIA_BY_USER_ID_MEDIA_TYPE_QUERY = """
    SELECT id, media_type, file_path, user_id
    FROM media
    WHERE user_id = :user_id and media_type = :media_type;
"""

GET_MEDIA_BY_ID_QUERY = """
    SELECT id, media_type, file_path, user_id
    FROM media
    WHERE id = :id;
"""

def mediaPublicFromDB(media: MediaInDB) -> MediaPublic:
    return MediaPublic(**media.copy(
        exclude={'file_path'},
        update={'url': get_url_by_path(media.file_path)}).dict())

class MediaRepository(BaseRepository):
    async def upload_media(self, *, media_upload: MediaUpload) -> MediaInDB:

        file_path = await save_file(
                file_type=FileType.media,
                media_type=media_upload.media_type,
                upload=media_upload.file)

        if media_upload.media_type == MediaType.avatar:
            prev_avatar = await self.get_user_avatar(user_id=media_upload.user_id)
            if prev_avatar:
                await self.delete_media(id=prev_avatar.id)

            #crop avatar image to square
            image_path = full_path(file_path)
            image = Image.open(image_path)
            if image.size[0] != image.size[1]:
                dm = min(image.size)
                image = image.crop((0, 0, dm, dm))
                image.save(image_path)

        created_media = await self.db.fetch_one(query=CREATE_MEDIA_QUERY, 
                values=media_upload.copy(exclude={'file'}, update={'file_path': file_path}).dict())

        return MediaInDB(**created_media)

    async def get_media_by_user_id_media_type(self, *, 
            user_id: int, media_type: MediaType) -> List[MediaInDB]:
        media_records = await self.db.fetch_all(query=GET_MEDIA_BY_USER_ID_MEDIA_TYPE_QUERY, 
                values={"user_id": user_id, "media_type": media_type})

        if not media_records:
            return None

        return [MediaInDB(**media_record) for media_record in media_records]

    async def get_media_by_id(self, *, id: int) -> MediaInDB:
        media_record = await self.db.fetch_one(query=GET_MEDIA_BY_ID_QUERY, 
                values={"id": id})

        if not media_record:
            return None

        return MediaInDB(**media_record)


    async def delete_media(self, *, id: int) -> None:
        media_record = await self.get_media_by_id(id=id)
        if media_record:
            await self.db.execute(query=DELETE_MEDIA_QUERY, values={"id": id})
            delete_file(media_record.file_path)

    async def get_user_avatar(self, *, user_id: int) -> MediaInDB:
        media_records = await self.get_media_by_user_id_media_type(user_id=user_id, media_type=MediaType.avatar)
        if media_records:
            return media_records[0]

        return None

    async def get_user_avatar_url(self, *, user_id) -> str:
        avatar = await self.get_user_avatar(user_id=user_id)
        if avatar:
            return get_url_by_path(avatar.file_path)

        return None


