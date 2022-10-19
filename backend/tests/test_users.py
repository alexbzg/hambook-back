import pytest
from typing import List, Union, Type, Optional
import jwt

from pydantic import ValidationError
from starlette.datastructures import Secret
from httpx import AsyncClient
from fastapi import FastAPI

from starlette.status import (
    HTTP_200_OK, 
    HTTP_201_CREATED, 
    HTTP_400_BAD_REQUEST, 
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND, 
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.models.user import UserCreate, UserInDB, UserPublic
from app.services import auth_service
from databases import Database
from app.db.repositories.users import UsersRepository
from app.core.config import SECRET_KEY, JWT_ALGORITHM, JWT_AUDIENCE, JWT_TOKEN_PREFIX, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.token import JWTMeta, JWTCreds, JWTPayload


pytestmark = pytest.mark.asyncio


class TestUserRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        new_user = {"email": "test@email.io", "password": "testpassword"}
        res = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert res.status_code != HTTP_404_NOT_FOUND

class TestUserRegistration:

    async def test_users_can_register_successfully(
        self, 
        app: FastAPI, 
        client: AsyncClient,
        db: Database,
    ) -> None:
        user_repo = UsersRepository(db)
        new_user = {"email": "aaa@bbb.cc", "password": "12345678"}
        # make sure user doesn't exist yet
        user_in_db = await user_repo.get_user_by_email(email=new_user["email"])
        assert user_in_db is None        
        # send post request to create user and ensure it is successful
        res = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert res.status_code == HTTP_201_CREATED
        # ensure that the user now exists in the db
        user_in_db = await user_repo.get_user_by_email(email=new_user["email"])
        assert user_in_db is not None
        assert user_in_db.email == new_user["email"]
        # check that the user returned in the response is equal to the user in the database
        created_user = UserPublic(**res.json()).dict(exclude={"access_token", "created_at", "updated_at"})
        assert created_user == user_in_db.dict(exclude={"password", "salt", "created_at", "updated_at"})
    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
            ("email", "aaa@bbb.cc", 400),            
            ("email", "invalid_email@one@two.io", 422),
            ("password", "short", 422)
        )
    )
    async def test_user_registration_fails_when_credentials_are_taken(
        self, 
        app: FastAPI, 
        client: AsyncClient,
        db: Database,
        attr: str,
        value: str,
        status_code: int,
    ) -> None: 
        new_user = {"email": "nottaken@email.io", "password": "freepassword"}
        new_user[attr] = value
        res = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert res.status_code == status_code

   
class TestAuthTokens:

    async def test_can_create_access_token_successfully(
        self, app: FastAPI, client: AsyncClient, test_user: UserInDB
    ) -> None:
        access_token = auth_service.create_access_token_for_user(
            user=test_user,
            secret_key=str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        creds = jwt.decode(access_token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])
        assert creds["id"] == test_user.id
        assert creds["aud"] == JWT_AUDIENCE

    async def test_token_missing_user_is_invalid(self, app: FastAPI, client: AsyncClient) -> None:
        access_token = auth_service.create_access_token_for_user(
            user=None,
            secret_key=str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        with pytest.raises(jwt.PyJWTError):
            jwt.decode(access_token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])

    @pytest.mark.parametrize(
        "secret_key, jwt_audience, exception",
        (
            ("wrong-secret", JWT_AUDIENCE, jwt.InvalidSignatureError),
            (None, JWT_AUDIENCE, jwt.InvalidSignatureError),
            (SECRET_KEY, "othersite:auth", jwt.InvalidAudienceError),
            (SECRET_KEY, None, ValidationError),
        )
    )
    async def test_invalid_token_content_raises_error(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: UserInDB,
        secret_key: Union[str, Secret],
        jwt_audience: str,
        exception: Type[BaseException],
    ) -> None:
        with pytest.raises(exception):
            access_token = auth_service.create_access_token_for_user(
                user=test_user,
                secret_key=str(secret_key),
                audience=jwt_audience,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
            )
            jwt.decode(access_token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])


class TestUserLogin:
    async def test_user_can_login_successfully_and_receives_valid_token(
        self, app: FastAPI, client: AsyncClient, test_user: UserInDB, test_user_password_plain: string
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        login_data = {
            "email": test_user.email,
            "password": test_user_password_plain
        }
        res = await client.post(app.url_path_for("users:login-email-and-password"), data=login_data)
        assert res.status_code == HTTP_200_OK
        # check that token exists in response and has user encoded within it
        token = res.json().get("access_token")
        creds = jwt.decode(token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])
        assert "sub" in creds
        assert creds["sub"] == test_user.email
		assert "id" in creds
		assert creds["id"] == test_user.id
        # check that token is proper type
        assert "token_type" in res.json()
        assert res.json().get("token_type") == "bearer"

    @pytest.mark.parametrize(
        "credential, wrong_value, status_code",
        (
            ("email", "wrong@email.com", 401),
            ("email", None, 401),
            ("email", "notemail", 401),
            ("password", "wrongpassword", 401),
            ("password", None, 401),
        ),
    )
    async def test_user_with_wrong_creds_doesnt_receive_token(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: UserInDB,
        credential: str,
        wrong_value: str,
        status_code: int,
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        user_data = test_user.dict()
        user_data["password"] = "heatcavslakers"  # insert user's plaintext password
        user_data[credential] = wrong_value
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"],  # insert password from parameters
        }

        res = await client.post(app.url_path_for("users:login-email-and-password"), data=login_data)
        assert res.status_code == status_code
        assert "access_token" not in res.json()

 
