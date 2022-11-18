import warnings
import os

import pytest

from fastapi import FastAPI
from databases import Database
from async_asgi_testclient import TestClient

import alembic
from alembic.config import Config

from app.models.user import UserCreate, UserInDB
from app.models.profile import ProfileUpdate
from app.db.repositories.users import UsersRepository
from app.db.repositories.profiles import ProfilesRepository

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

@pytest.fixture
async def test_user(db: Database, test_user_password_plain: str, test_user_callsign: str) -> UserInDB:
    new_user = UserCreate(
        email="alexbzg@gmail.com",
        password=test_user_password_plain
    )
    user_repo = UsersRepository(db)
    existing_user = await user_repo.get_user_by_email(email=new_user.email, populate=False)
    if existing_user:
        return existing_user
    profile_repo = ProfilesRepository(db)
    test_user = await user_repo.register_new_user(new_user=new_user)
    await profile_repo.update_profile(
            requesting_user=test_user, 
            profile_update=ProfileUpdate(current_callsign=test_user_callsign))
    return test_user


