import pytest
from datetime import date

from fastapi import FastAPI, status
from async_asgi_testclient import TestClient

from databases import Database
from app.models.user import UserInDB, UserPublic
from app.models.profile import ProfileInDB, ProfilePublic
from app.db.repositories.profiles import ProfilesRepository


pytestmark = pytest.mark.asyncio


class TestProfilesRoutes:
    """
    Ensure that no api route returns a 404
    """

    async def test_routes_exist(self, 
            app: FastAPI, 
            client: TestClient, 
            test_user: UserInDB,
            test_user_callsign: str) -> None:
        # Get profile by username
        res = await client.get(app.url_path_for("profiles:get-profile-by-user_id", user_id=test_user.id))
        assert res.status_code != status.HTTP_404_NOT_FOUND

        res = await client.get(app.url_path_for("profiles:get-profile-by-callsign", callsign=test_user_callsign))
        assert res.status_code != status.HTTP_404_NOT_FOUND

        # Update own profile
        res = await client.put(app.url_path_for("profiles:update-own-profile"), json={"profile_update": {}})
        assert res.status_code != status.HTTP_404_NOT_FOUND


class TestProfileCreate:
    async def test_profile_created_for_new_users(self, app: FastAPI, client: TestClient, db: Database) -> None:
        profiles_repo = ProfilesRepository(db)
        new_user = {"email": "profiles_aaa@bbb.cc", "password": "12345678"}
        res = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert res.status_code == status.HTTP_201_CREATED
        created_user = UserPublic(**res.json())
        user_profile = await profiles_repo.get_profile_by_user_id(user_id=created_user.id)
        assert user_profile is not None
        assert isinstance(user_profile, ProfileInDB)        

# ...other code


class TestProfileView:
    async def test_can_view_users_profile(
        self, app: FastAPI, client: TestClient, test_user: UserInDB) -> None:
        res = await client.get(
            app.url_path_for("profiles:get-profile-by-user_id", user_id=test_user.id)
        )
        assert res.status_code == status.HTTP_200_OK
        profile = ProfilePublic(**res.json())
        assert profile.user_id == test_user.id

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


