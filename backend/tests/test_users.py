import pytest
from typing import List, Union, Type, Optional
import jwt

from pydantic import ValidationError
from starlette.datastructures import Secret
from fastapi import FastAPI, HTTPException, status
from async_asgi_testclient import TestClient

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


pytestmark = pytest.mark.anyio


class TestUserRoutes:
    async def test_routes_exist(self, app: FastAPI, client: TestClient) -> None:
        new_user = {"email": "test@email.io", "password": "testpassword"}
        res = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert res.status_code != HTTP_404_NOT_FOUND

class TestUserRegistration:

    async def test_users_can_register_successfully(
        self, 
        app: FastAPI, 
        client: TestClient,
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
        user_in_db = await user_repo.get_user_by_email(email=new_user["email"], populate=False)
        assert user_in_db is not None
        assert user_in_db.email == new_user["email"]
        # check that the user returned in the response is equal to the user in the database
        created_user = UserPublic(**res.json()).dict(exclude={"access_token", "created_at", "updated_at", "profile"})
        created_user["id"] = int(created_user["id"])
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
        client: TestClient,
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
        self, app: FastAPI, client: TestClient, test_user: UserInDB
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

    async def test_token_missing_user_is_invalid(self, app: FastAPI, client: TestClient) -> None:
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
        client: TestClient,
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

    async def test_can_retrieve_userid_from_token(
        self, app: FastAPI, client: TestClient, test_user: UserInDB
    ) -> None:
        token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
        userid = auth_service.get_userid_from_token(token=token, secret_key=str(SECRET_KEY))
        assert userid == test_user.id


    @pytest.mark.parametrize(
        "secret, wrong_token",
        (
            (SECRET_KEY, "asdf"),  # use wrong token
            (SECRET_KEY, ""),  # use wrong token
            (SECRET_KEY, None),  # use wrong token
            ("ABC123", "use correct token"),  # use wrong secret
        ),
    )
    async def test_error_when_token_or_secret_is_wrong(
        self,
        app: FastAPI,
        client: TestClient,
        test_user: UserInDB,
        secret: Union[Secret, str],
        wrong_token: Optional[str],
    ) -> None:
        token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
        if wrong_token == "use correct token":
            wrong_token = token
        with pytest.raises(HTTPException):
            username = auth_service.get_username_from_token(token=wrong_token, secret_key=str(secret))    

    async def test_can_retrieve_userid_from_token(
        self, app: FastAPI, client: TestClient, test_user: UserInDB
    ) -> None:
        token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
        userid = auth_service.get_userid_from_token(token=token, secret_key=str(SECRET_KEY))
        assert userid == test_user.id

    @pytest.mark.parametrize(
        "secret, wrong_token",
        (
            (SECRET_KEY, "asdf"),  # use wrong token
            (SECRET_KEY, ""),  # use wrong token
            (SECRET_KEY, None),  # use wrong token
            ("ABC123", "use correct token"),  # use wrong secret
        ),
    )
    async def test_error_when_token_or_secret_is_wrong(
        self,
        app: FastAPI,
        client: TestClient,
        test_user: UserInDB,
        secret: Union[Secret, str],
        wrong_token: Optional[str],
    ) -> None:
        token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
        if wrong_token == "use correct token":
            wrong_token = token
        with pytest.raises(HTTPException):
            userid = auth_service.get_userid_from_token(token=wrong_token, secret_key=str(secret))    


class TestUserLogin:
	async def test_user_can_login_successfully_and_receives_valid_token(
		self, app: FastAPI, client: TestClient, test_user: UserInDB, test_user_password_plain: str
	) -> None:
		client.headers["content-type"] = "application/x-www-form-urlencoded"
		login_data = {
			"username": test_user.email,
			"password": test_user_password_plain
		}
		res = await client.post(app.url_path_for("users:login-email-and-password"), form=login_data)
		assert res.status_code == HTTP_200_OK
# check that token exists in response and has user encoded within it
		token = res.json().get("access_token")
		creds = jwt.decode(token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])
		assert "sub" in creds
		assert creds["sub"] == test_user.email
		assert "id" in creds
		assert creds["id"] == test_user.id
		assert "type" in creds
		assert creds["type"] == "bearer"
# check that token is proper type
		assert "token_type" in res.json()
		assert res.json().get("token_type") == "bearer"

	@pytest.mark.parametrize("credential, wrong_value, status_code",
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
		client: TestClient,
		test_user: UserInDB,
		test_user_password_plain: str,
		credential: str,
		wrong_value: str,
		status_code: int,
	) -> None:
		client.headers["content-type"] = "application/x-www-form-urlencoded"
		user_data = test_user.dict()
		user_data["password"] = test_user_password_plain
		user_data[credential] = wrong_value
		login_data = {
			"username": user_data["email"],
			"password": user_data["password"],  # insert password from parameters
		}

		res = await client.post(app.url_path_for("users:login-email-and-password"), form=login_data)
		assert res.status_code == status_code
		assert "access_token" not in res.json()


class TestUserMe:
    async def test_authenticated_user_can_retrieve_own_data(
        self, app: FastAPI, authorized_client: TestClient, test_user: UserInDB,
    ) -> None:
        res = await authorized_client.get(app.url_path_for("users:get-current-user"))
        assert res.status_code == HTTP_200_OK
        user = UserPublic(**res.json())
        assert user.email == test_user.email
        assert int(user.id) == int(test_user.id)

    async def test_user_cannot_access_own_data_if_not_authenticated(
        self, app: FastAPI, client: TestClient, test_user: UserInDB,
    ) -> None:
        res = await client.get(app.url_path_for("users:get-current-user"))
        assert res.status_code == HTTP_401_UNAUTHORIZED


    @pytest.mark.parametrize("jwt_prefix", (("",), ("value",), ("Token",), ("JWT",), ("Swearer",),))
    async def test_user_cannot_access_own_data_with_incorrect_jwt_prefix(
        self, app: FastAPI, client: TestClient, test_user: UserInDB, jwt_prefix: str,
    ) -> None:
        token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
        res = await client.get(
            app.url_path_for("users:get-current-user"), headers={"Authorization": f"{jwt_prefix} {token}"}
        )
        assert res.status_code == HTTP_401_UNAUTHORIZED

class TestEmailVerification:
    async def test_authenticated_user_can_request_email_verification(
        self, app: FastAPI, authorized_client: TestClient, test_user: UserInDB,
    ) -> None:
        res = await authorized_client.get(app.url_path_for("users:email-verification-request"))
        assert res.status_code == HTTP_200_OK

    async def test_user_cannot_request_email_verification_when_not_authenticated(
        self, app: FastAPI, client: TestClient, test_user: UserInDB,
    ) -> None:
        res = await client.get(app.url_path_for("users:email-verification-request"))
        assert res.status_code == HTTP_401_UNAUTHORIZED

    async def test_user_can_verify_email(
        self, 
        app: FastAPI, 
        client: TestClient,
        db: Database,
        test_user: UserInDB
        ) -> None:
        token = auth_service.create_access_token_for_user(
                user=test_user, 
                secret_key=str(SECRET_KEY), 
                token_type='email verification')
        res = await client.get(app.url_path_for("users:email-verification", token=token))
        assert res.status_code == HTTP_200_OK
        user_repo = UsersRepository(db)
        user_in_db = await user_repo.get_user_by_email(email=test_user.email)
        assert user_in_db.email_verified

    async def test_user_cannnot_verify_email_if_already_verified(
        self, 
        app: FastAPI, 
        client: TestClient,
        db: Database,
        test_user: UserInDB
        ) -> None:
        token = auth_service.create_access_token_for_user(
                user=test_user, 
                secret_key=str(SECRET_KEY), 
                token_type='email verification')
        user_repo = UsersRepository(db)
        if not test_user.email_verified:
            await user_repo.verify_user_email(userid=test_user.id)
        res = await client.get(app.url_path_for("users:email-verification", token=token))
        assert res.status_code == HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "secret, wrong_token, token_type",
        (
            (SECRET_KEY, "asdf", "email verification"),  # use wrong token
            (SECRET_KEY, None, "email verification"),  # use wrong token
            ("ABC123", "use correct token", "email verification"),  # use wrong secret
            (SECRET_KEY, "use correct token", "bearer"),  # use wrong token type
        ),
    )
    async def test_users_cannot_verify_email_when_token_or_secret_is_wrong(
        self,
        app: FastAPI,
        client: TestClient,
        db: Database,
        test_user: UserInDB,
        secret: Union[Secret, str],
        wrong_token: Optional[str],
        token_type: str,
        ) -> None:
        user_repo = UsersRepository(db)
        if test_user.email_verified:
            await user_repo.update_user(user=test_user, update_params={'email_verified': False})
        token = auth_service.create_access_token_for_user(
                user=test_user, 
                secret_key=str(secret), 
                token_type=token_type) if wrong_token == "use correct token" else wrong_token
        res = await client.get(app.url_path_for("users:email-verification", token=token))
        assert res.status_code == HTTP_401_UNAUTHORIZED

class TestPasswordReset:
    async def test_user_can_request_password_reset(
        self, app: FastAPI, client: TestClient, test_user: UserInDB,
    ) -> None:
        res = await client.get(app.url_path_for("users:password-reset-request", email=test_user.email))
        assert res.status_code == HTTP_200_OK

    async def test_user_cannot_request_password_reset_with_wrong_email(
        self, app: FastAPI, client: TestClient,
    ) -> None:
        res = await client.get(app.url_path_for("users:password-reset-request", email="wrong@email.com"))
        assert res.status_code == HTTP_400_BAD_REQUEST

    async def test_user_can_reset_password(
        self, 
        app: FastAPI, 
        client: TestClient,
        db: Database,
        test_user: UserInDB
        ) -> None:
        token = auth_service.create_access_token_for_user(
                user=test_user, 
                secret_key=str(SECRET_KEY), 
                token_type='password reset')
        new_password = "18181818"
        res = await client.post(app.url_path_for("users:password-reset"), 
            json={"password_reset": {"token": token, "password": new_password}})
        assert res.status_code == HTTP_200_OK
        user_repo = UsersRepository(db)
        if test_user.email_verified:
            await user_repo.update_user(user=test_user, update_params={'email_verified': False})
        user_in_db = await user_repo.authenticate_user(email=test_user.email, password=new_password)
        assert user_in_db
        assert user_in_db.email_verified

    @pytest.mark.parametrize(
        "secret, wrong_token, token_type",
        (
            (SECRET_KEY, "asdf", "password reset"),  # use wrong token
            (SECRET_KEY, None, "password reset"),  # use wrong token
            ("ABC123", "use correct token", "password reset"),  # use wrong secret
            (SECRET_KEY, "use correct token", "bearer"),  # use wrong token type
        ),
    )
    async def test_users_cannot_reset_password_when_token_or_secret_is_wrong(
        self,
        app: FastAPI,
        client: TestClient,
        db: Database,
        test_user: UserInDB,
        secret: Union[Secret, str],
        wrong_token: Optional[str],
        token_type: str,
        ) -> None:
        token = auth_service.create_access_token_for_user(
                user=test_user, 
                secret_key=str(secret), 
                token_type=token_type) if wrong_token == "use correct token" else wrong_token
        res = await client.post(app.url_path_for("users:password-reset"), 
                json={'password_reset': {"token": token, "password": "18181818"}})
        res = await client.get(app.url_path_for("users:email-verification", token=token))
        assert res.status_code == HTTP_401_UNAUTHORIZED

