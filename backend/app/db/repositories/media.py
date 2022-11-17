from typing import List

from app.db.repositories.base import BaseRepository
from app.models.media import MediaCreate, MediaInDB, MediaType
from app.models.user import UserInDB
from app.services.static_files import delete_file

CREATE_MEDIA_QUERY = """
    INSERT INTO media (media_type, file_path, user_id)
    VALUES (:media_type, :file_path, :user_id), 
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

class MediaRepository(BaseRepository):
    async def create_media(self, *, media_create: MediaCreate) -> MediaInDB:
        created_media = await self.db.fetch_one(query=CREATE_MEDIA_QUERY, values=media_create.dict())

        return created_media

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
        media_record = self.get_media_by_id(id=id)
        if media_record:
            await self.db.execute(query=DELETE_MEDIA_QUERY, values={"id": id})
            delete_file(media_record.file_path)


