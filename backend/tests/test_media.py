import pytest

from fastapi import FastAPI, status
from async_asgi_testclient import TestClient

from databases import Database
from app.models.user import UserInDB, UserPublic
from app.models.media import MediaInDB, MediaPublic, MediaType
from app.db.repositories.media import MediaRepository
from app.db.repositories.profiles import ProfilesRepository


pytestmark = pytest.mark.asyncio


class TestMediaUpload:
    async def test_user_can_upload_media(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        test_user: UserInDB,
        db: Database) -> None:
        media_repo = MediaRepository(db)
        with open('/backend/tests/files/user.jpg', 'rb') as file:
            res = await authorized_client.post(app.url_path_for("media:upload"), 
                headers={"content-type": "multipart/form-data"},
                files={
                    "media_type": str(int(MediaType.avatar)),
                    "file": ("user.jpg", file,'image/jpeg')
                    }
            )
        assert res.status_code == status.HTTP_201_CREATED
        media = MediaPublic(**res.json())
        media_in_db = await media_repo.get_media_by_id(id=int(media.id))
        assert media_in_db is not None
        assert media_in_db.user_id == int(test_user.id)

    async def test_unauthorized_user_can_not_upload_media(self, *,
        app: FastAPI, 
        client: TestClient,
        test_user: UserInDB,
        db: Database) -> None:
        media_repo = MediaRepository(db)
        with open('/backend/tests/files/user.jpg', 'rb') as file:
            res = await client.post(app.url_path_for("media:upload"), 
                headers={"content-type": "multipart/form-data"},
                files={
                    "media_type": str(int(MediaType.avatar)),
                    "file": ("user.jpg", file,'image/jpeg')
                    }
            )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_prev_avatar_is_deletes_after_new_upload(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        test_user: UserInDB,
        db: Database) -> None:
        media_repo = MediaRepository(db)
        
        with open('/backend/tests/files/user.jpg', 'rb') as file:
            res = await authorized_client.post(app.url_path_for("media:upload"), 
                headers={"content-type": "multipart/form-data"},
                files={
                    "media_type": str(int(MediaType.avatar)),
                    "file": ("user.jpg", file,'image/jpeg')
                    }
            )
        assert res.status_code == status.HTTP_201_CREATED
        media = MediaPublic(**res.json())
        media_in_db = await media_repo.get_media_by_id(id=int(media.id))
        assert media_in_db.user_id == int(test_user.id)
        assert media_in_db is not None
        avatars_in_db = await media_repo.get_media_by_user_id_media_type(user_id=int(test_user.id), 
                media_type=MediaType.avatar)
        assert len(avatars_in_db) == 1
        assert avatars_in_db[0] == media_in_db


# ...other code


class TestProfileView:
    async def test_can_view_users_profile(
        self, app: FastAPI, client: TestClient, test_user: UserInDB) -> None:
        res = await client.get(
            app.url_path_for("profiles:get-profile-by-user_id", user_id=test_user.id)
        )
        assert res.status_code == status.HTTP_200_OK
        profile = ProfilePublic(**res.json())
        assert int(profile.user_id) == test_user.id

    async def test_no_profile_is_returned_when_userid_matches_no_user(
        self, app: FastAPI, client: TestClient
    ) -> None:
        res = await client.get(
            app.url_path_for("profiles:get-profile-by-user_id", user_id="1234")
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND          

    async def test_no_profile_is_returned_when_callsign_matches_no_user(
        self, app: FastAPI, client: TestClient
    ) -> None:
        res = await client.get(
            app.url_path_for("profiles:get-profile-by-callsign", callsign="bad000cs")
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND          



class TestProfileManagement:


    @pytest.mark.parametrize(
        "attr, value",
        (
            ("full_name", "John Doe"),
            ("address", "somewhere"),
            ("bio", "This is a test bio"),
			("current_callsign", "SM1CS"),
			("prev_callsigns", "SM2CS SM3CS"),
			("birthdate", '2019-12-04')
        ),
    )
    async def test_user_can_update_own_profile(
            self, 
            app: FastAPI, 
            authorized_client: TestClient, 
            db: Database, 
            test_user: UserInDB, 
            attr: str, 
            value: str,
    ) -> None:
        profiles_repo = ProfilesRepository(db)        
        test_user_profile = await profiles_repo.get_profile_by_user_id(user_id=test_user.id)
        assert getattr(test_user_profile, attr) != value
        res = await authorized_client.put(
            app.url_path_for("profiles:update-own-profile"), json={"profile_update": {attr: value}},
        )
        assert res.status_code == status.HTTP_200_OK
        profile = ProfilePublic(**res.json())
        if attr != 'birthdate':
            assert getattr(profile, attr) == value


    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
            ("full_name", [], 422),
            ("bio", {}, 422),
            ("current_callsign", "bad callsign", 422),
        ),
    )
    async def test_user_recieves_error_for_invalid_update_params(
        self, 
        app: FastAPI, 
        authorized_client: TestClient, 
        test_user: UserInDB, 
        attr: str, 
        value: str, 
        status_code: int,
    ) -> None:
        res = await authorized_client.put(
            app.url_path_for("profiles:update-own-profile"), json={"profile_update": {attr: value}},
        )
        assert res.status_code == status_code


