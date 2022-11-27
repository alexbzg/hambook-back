import warnings
import os
from typing import Callable

import pytest

from fastapi import FastAPI
from databases import Database
from async_asgi_testclient import TestClient

import alembic
from alembic.config import Config

from app.models.user import UserCreate, UserInDB
from app.models.profile import ProfileUpdate
from app.models.media import MediaType
from app.db.repositories.users import UsersRepository
from app.db.repositories.profiles import ProfilesRepository
from app.db.repositories.media import MediaRepository

from app.core.config import SECRET_KEY, JWT_TOKEN_PREFIX
from app.services import auth_service

@pytest.fixture
def test_user_password_plain() -> str:
    return "12345678"

@pytest.fixture
def test_user_callsign() -> str:
    return "TE1ST"

# Make requests in our tests
@pytest.fixture
async def client(app: FastAPI) -> TestClient:
    async with TestClient(app) as client:
        yield client

@pytest.fixture
def authorized_client(client: TestClient, test_user: UserInDB) -> TestClient:
    access_token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
    client.headers = {
        **client.headers,
        "Authorization": f"{JWT_TOKEN_PREFIX} {access_token}",
    }
    return client

# Apply migrations at beginning and end of testing session
@pytest.fixture(scope="session")
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")

    alembic.command.upgrade(config, "head")
    yield
    alembic.command.downgrade(config, "base")


# Create a new application for testing
@pytest.fixture
def app(apply_migrations: None) -> FastAPI:
    from app.api.server import get_application

    return  get_application()


# Grab a reference to our database when needed
@pytest.fixture
def db(app: FastAPI) -> Database:
    return app.state._db

async def user_fixture_helper(*, db: Database, new_user: UserCreate) -> UserInDB:
	user_repo = UsersRepository(db)

	user = await user_repo.get_user_by_email(email=new_user.email, populate=False)
	if not user:
		await user_repo.register_new_user(new_user=new_user)
		user = await user_repo.get_user_by_email(email=new_user.email, populate=False)

	return user

async def user_media_cleanup(*, db: Database, user: UserInDB) -> None:
    media_repo = MediaRepository(db)
    media_types = [x.value for x in MediaType]
    for media_type in media_types:
        medias = await media_repo.get_media_by_user_id_media_type(user_id=user.id, media_type=media_type)
        if medias:
            for media in medias:
                await media_repo.delete_media(id=media.id)

@pytest.fixture
async def test_user(db: Database, test_user_password_plain: str, test_user_callsign: str) -> UserInDB:
    new_user = UserCreate(
        email="alexbzg@gmail.com",
        password=test_user_password_plain
    )
    test_user = await user_fixture_helper(db=db, new_user=new_user)
    profile_repo = ProfilesRepository(db)
    await profile_repo.update_profile(
        requesting_user=test_user, 
        profile_update=ProfileUpdate(current_callsign=test_user_callsign))
    yield test_user
    await user_media_cleanup(db=db, user=test_user)
    

@pytest.fixture
async def test_user2(db: Database) -> UserInDB:
	new_user = UserCreate(
		email="18@73.ru",
		password="12121212"
	)
	return await user_fixture_helper(db=db, new_user=new_user)

@pytest.fixture
def create_authorized_client(client: TestClient) -> Callable:
	def _create_authorized_client(*, user: UserInDB) -> TestClient:
		access_token = auth_service.create_access_token_for_user(user=user, secret_key=str(SECRET_KEY))

		client.headers = {
			**client.headers,
			"Authorization": f"{JWT_TOKEN_PREFIX} {access_token}",
		}

		return client

	return _create_authorized_client

