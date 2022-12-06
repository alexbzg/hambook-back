from os import path
from typing import Callable

import pytest

from fastapi import FastAPI, status
from async_asgi_testclient import TestClient
from async_asgi_testclient.response import Response

from databases import Database
from app.models.user import UserInDB, UserPublic
from app.models.media import MediaInDB, MediaPublic, MediaType
from app.db.repositories.media import MediaRepository
from app.db.repositories.profiles import ProfilesRepository

pytestmark = pytest.mark.anyio

async def upload_media_helper(*, 
        app: FastAPI,
        client: TestClient,
        media_type: MediaType,
        file_path: str) -> Response:
    with open(file_path, 'rb') as file:
        file_name = path.basename(file_path)
        return await client.post(app.url_path_for("media:upload"), 
            headers={"content-type": "multipart/form-data"},
            files={
                "media_type": str(int(media_type)),
                "file": (file_name, file,'image/jpeg')
                }
        )

@pytest.fixture
async def avatar_upload(
        app: FastAPI,
        db: Database, 
        test_user: UserInDB,
        authorized_client: TestClient) -> MediaPublic:
    res = await upload_media_helper(
            app=app, 
            client=authorized_client,
            media_type=MediaType.avatar,
            file_path='/backend/tests/files/user.jpg') 
    return MediaPublic(**res.json())

class TestMediaUpload:
    async def test_user_can_upload_media(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        test_user: UserInDB,
        db: Database,
        avatar_upload: MediaPublic) -> None:

        media_repo = MediaRepository(db)
        media_in_db = await media_repo.get_media_by_id(id=int(avatar_upload.id))
        assert media_in_db is not None
        assert media_in_db.user_id == int(test_user.id)
        assert media_in_db.id == int(avatar_upload.id)

    async def test_unauthorized_user_can_not_upload_media(self, *,
        app: FastAPI, 
        client: TestClient,
        test_user: UserInDB,
        db: Database) -> None:
        media_repo = MediaRepository(db)

        res = await upload_media_helper(
                app=app, 
                client=client,
                media_type=MediaType.avatar,
                file_path='/backend/tests/files/user.jpg') 
       
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_prev_avatar_is_deleted_after_new_upload(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        test_user: UserInDB,
        db: Database,
        avatar_upload: MediaPublic) -> None:

        res = await upload_media_helper(
                app=app, 
                client=authorized_client,
                media_type=MediaType.avatar,
                file_path='/backend/tests/files/user.jpg') 
        assert res.status_code == status.HTTP_201_CREATED
        new_avatar = MediaPublic(**res.json())
        assert new_avatar.id != avatar_upload.id

        media_repo = MediaRepository(db)
        media_in_db = await media_repo.get_media_by_id(id=int(new_avatar.id))
        assert media_in_db.user_id == int(test_user.id)
        assert media_in_db is not None
        avatars_in_db = await media_repo.get_media_by_user_id_media_type(user_id=int(test_user.id), 
                media_type=MediaType.avatar)
        assert len(avatars_in_db) == 1
        assert avatars_in_db[0] == media_in_db

class TestMediaDelete:
    
    async def test_user_can_delete_media(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        test_user: UserInDB,
        db: Database,
        avatar_upload: MediaPublic) -> None:

        res = await authorized_client.delete(app.url_path_for("media:delete", 
            media_id=avatar_upload.id)) 

        assert res.status_code == status.HTTP_200_OK

        media_repo = MediaRepository(db)
        media_in_db = await media_repo.get_media_by_id(id=int(avatar_upload.id))
        assert media_in_db is None

        profiles_repo = ProfilesRepository(db)
        test_user_profile = await profiles_repo.get_profile_by_user_id(user_id=test_user.id)
        assert test_user_profile.avatar is None

    async def test_user_cannot_delete_not_owned_media(self, *,
        app: FastAPI,
        authorized_client: TestClient,
        test_user: UserInDB,
        test_user2: UserInDB,
        create_authorized_client: Callable,
        db: Database,
        avatar_upload: MediaPublic) -> None:

        test_user2_client = create_authorized_client(user=test_user2)

        res = await test_user2_client.delete(app.url_path_for("media:delete", 
            media_id=avatar_upload.id)) 
        assert res.status_code == status.HTTP_403_FORBIDDEN

class TestMediaQuery:

    async def test_media_query_existing(self, *,
        app: FastAPI,
        authorized_client: TestClient,
        client: TestClient,
        test_user: UserInDB,
        test_user2: UserInDB,
        db: Database,
        avatar_upload: MediaPublic) -> None:

        res = await client.get(app.url_path_for("media:query-by-user-and-type", 
            user_id=test_user.id,
            media_type=int(MediaType.avatar)))
        assert res.status_code == status.HTTP_200_OK

        medias = [MediaPublic(**item) for item in res.json()]
        assert len(medias) == 1
        assert (medias[0].dict(exclude={'created_at', 'updated_at'}) == 
            avatar_upload.dict(exclude={'created_at', 'updated_at'}))

    async def test_media_query_non_existing(self, *,
        app: FastAPI,
        authorized_client: TestClient,
        client: TestClient,
        test_user: UserInDB,
        test_user2: UserInDB,
        db: Database,
        avatar_upload: MediaPublic) -> None:

        res = await client.get(app.url_path_for("media:query-by-user-and-type", 
            user_id=test_user2.id,
            media_type=int(MediaType.avatar)))
        assert res.status_code == status.HTTP_404_NOT_FOUND

        res = await client.get(app.url_path_for("media:query-by-user-and-type", 
            user_id=test_user2.id,
            media_type=int(MediaType.profile_media)))
        assert res.status_code == status.HTTP_404_NOT_FOUND
       
