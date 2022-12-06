from os import path
from typing import Callable

import pytest

from fastapi import FastAPI, status
from async_asgi_testclient import TestClient
from async_asgi_testclient.response import Response

from databases import Database
from app.models.user import UserInDB, UserPublic
from app.models.qso_log import QsoLogBase, QsoLogInDB
from app.db.repositories.qso_logs import QsoLogsRepository

pytestmark = pytest.mark.asyncio

class TestQsoLogCreate:
    async def test_user_can_create_qso_log(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        test_user: UserInDB,
        db: Database,
        test_qso_log_created: QsoLogInDB) -> None:

        assert test_qso_log_created
        assert test_qso_log_created.id
        assert test_qso_log_created.user_id == test_user.id

class TestQsoLogDelete:
    
    async def test_user_can_delete_logs_they_own(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        test_user: UserInDB,
        db: Database,
        test_qso_log_created: QsoLogInDB) -> None:

        res = await authorized_client.delete(app.url_path_for("qso-logs:delete-log", 
            log_id=test_qso_log_created.id)) 

        assert res.status_code == status.HTTP_200_OK

        qso_logs_repo = QsoLogsRepository(db)
        qso_log_in_db = await qso_logs_repo.get_log_by_id(id=test_qso_log_created.id)
        assert qso_log_in_db is None

    async def test_user_cannot_delete_non_existent_logs(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        test_user: UserInDB,
        db: Database,
        test_qso_log_created: QsoLogInDB) -> None:

        res = await authorized_client.delete(app.url_path_for("qso-logs:delete-log", 
            log_id=test_qso_log_created.id + 1)) 

        assert res.status_code == status.HTTP_404_NOT_FOUND

    async def test_user_cannot_delete_logs_they_do_not_own(self, *,
        app: FastAPI,
        authorized_client: TestClient,
        test_user: UserInDB,
        test_user2: UserInDB,
        create_authorized_client: Callable,
        db: Database,
        test_qso_log_created: QsoLogInDB) -> None:

        test_user2_client = create_authorized_client(user=test_user2)

        res = await test_user2_client.delete(app.url_path_for("qso-logs:delete-log", 
            log_id=test_qso_log_created.id))
        
        assert res.status_code == status.HTTP_403_FORBIDDEN

class TestQsoLogUpdate:
   
    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
            ("callsign", "ADM1N/M", 200),
            ("callsign", "bad callsign", 422),
            ("description", "another fake description", 200),
        ),
    )
    async def test_user_can_update_their_logs_and_get_error_on_invalid_fields(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        test_user: UserInDB,
        db: Database,
        test_qso_log_created: QsoLogInDB,
        attr: str,
        value: str,
        status_code: int)-> None:

        res = await authorized_client.put(app.url_path_for("qso-logs:update-log", 
            log_id=test_qso_log_created.id), 
            json={'log_update':{attr: value}}) 

        assert res.status_code == status_code

        if status_code == 200:
            updated_log = res.json()
            assert updated_log[attr] == value

class TestQsoLogView:

    async def test_clients_can_query_logs_by_user_id(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        client: TestClient,
        test_user: UserInDB,
        db: Database,
        test_qso_log_created: QsoLogInDB) -> None:

        res = await client.get(app.url_path_for("qso-logs:query-by-user", 
            user_id=test_user.id))

        assert res.status_code == 200        
        logs = [log for log in res.json() if int(log['id']) == test_qso_log_created.id]
        assert len(logs) == 1
        assert (QsoLogInDB(**logs[0]).dict(exclude={'created_at', 'updated_at'}) == 
                test_qso_log_created.dict(exclude={'created_at', 'updated_at'}))

    async def test_clients_can_query_logs_by_id(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        client: TestClient,
        test_user: UserInDB,
        db: Database,
        test_qso_log_created: QsoLogInDB) -> None:

        res = await client.get(app.url_path_for("qso-logs:query-by-log-id"), 
                query_string={'log_id': test_qso_log_created.id})

        assert res.status_code == 200        
        assert (QsoLogInDB(**res.json()).dict(exclude={'created_at', 'updated_at'}) == 
                test_qso_log_created.dict(exclude={'created_at', 'updated_at'}))

