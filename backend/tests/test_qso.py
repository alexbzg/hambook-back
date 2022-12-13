from os import path
from typing import Callable

import pytest

from fastapi import FastAPI, status
from async_asgi_testclient import TestClient
from async_asgi_testclient.response import Response

from databases import Database
from app.models.user import UserInDB, UserPublic
from app.models.qso_log import QsoLogInDB
from app.models.qso import QsoInDB, QsoBase

from app.db.repositories.qso import QsoRepository

pytestmark = pytest.mark.anyio

@pytest.fixture
async def test_qso_params():
    return {
        "callsign": "ADM1N/QRP",
        "station_callsign": "U3/R7CL/M",
        "qso_datetime": "2022-12-08T08:55:17.532Z",
        "band": "160M",
        "freq": 18000.59,
        "qso_mode": "CW",
        "rst_s": 599,
        "rst_r": 599,
        "name": "some name",
        "qth": "some city",
        "gridsquare": "aa11bb",
        "extra": {"foo": "bar"}
    }

async def qso_create_helper(
        app: FastAPI,
        client: TestClient,
        qso_params: dict,
        log_id: int) -> Response:
    
    return await client.post(
            app.url_path_for("qso:create-qso", log_id=log_id), 
            json={"new_qso": qso_params}
        )
   
async def qso_delete_helper(
        app: FastAPI,
        client: TestClient,
        qso_id: int) -> Response:
    
    return await client.delete(
            app.url_path_for("qso:delete-qso", qso_id=qso_id), 
        )
   
@pytest.fixture
async def test_qso_created(
        app: FastAPI,
        authorized_client: TestClient,
        test_qso_params: dict,
        test_qso_log_created: QsoLogInDB) -> QsoInDB:
    
    res = await qso_create_helper(
            app=app, 
            client=authorized_client, 
            qso_params=test_qso_params,
            log_id=test_qso_log_created.id
        ) 

    return QsoInDB(**res.json())

class TestQsoCreate:
    async def test_user_can_create_qso(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        test_user: UserInDB,
        test_qso_log_created: QsoLogInDB,
        test_qso_params: dict,
        test_qso_created: QsoInDB) -> None:

        assert test_qso_created
        assert test_qso_created.id
        assert test_qso_created.log_id == test_qso_log_created.id
        test_qso_dict = test_qso_created.dict()
        for field in test_qso_params:
            if field not in ("qso_datetime"):
                assert test_qso_params[field] == test_qso_dict[field]

    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
            ("callsign", "bsd callsign", 422),
            ("qso_datetime", "2022-02-31T08:55:17.532Z", 422),
            ("band", "320M", 422),
            ("qso_mode", "RTTY", 422),
            ("rst_s", None, 422),
            ("rst_r", "string", 422)
        ),
    )
    async def test_user_get_error_on_invalid_fields(self, *,
        app: FastAPI, 
        authorized_client: TestClient,
        test_user: UserInDB,
        attr: str,
        value: str,
        status_code: int,
        test_qso_log_created: QsoLogInDB,
        test_qso_params: dict,
        test_qso_created: QsoInDB) -> None:

        test_qso_params[attr] = value
        res = await qso_create_helper(
            app=app, 
            client=authorized_client, 
            qso_params=test_qso_params,
            log_id=test_qso_log_created.id
        ) 
        assert res.status_code == status_code

    async def test_unauthorized_user_cannot_create_qso(self, *,
        app: FastAPI, 
        create_authorized_client: Callable,
        test_qso_log_created: QsoLogInDB,
        test_qso_params: dict) -> None:

        client = create_authorized_client(user=None)
        res = await qso_create_helper(
            app=app, 
            client=client, 
            qso_params=test_qso_params,
            log_id=test_qso_log_created.id
        ) 
        assert res.status_code == 401

    async def test_user_cannot_create_qso_in_log_they_dont_own(self, *,
        app: FastAPI, 
        create_authorized_client: Callable,
        test_user2: UserInDB,
        test_qso_log_created: QsoLogInDB,
        test_qso_params: dict) -> None:

        client = create_authorized_client(user=test_user2)
        res = await qso_create_helper(
            app=app, 
            client=client, 
            qso_params=test_qso_params,
            log_id=test_qso_log_created.id
        ) 
        assert res.status_code == 403

class TestQsoDelete:
    
    @pytest.mark.parametrize(
        "attr, value, status_code, comments",
        (
            (None, None, 200, "ok"),
            ("user", 0, 403, "wrong user"),
            ("user", 1, 401, "unauthenticated"),
            ("qso_id", 18, 404, "nonexistent qso"),
        ),
    )
    async def test_delete_qso(self, *,
        app: FastAPI, 
        create_authorized_client: Callable,
        attr: str,
        value: str,
        status_code: int,
        comments: str,
        test_user: UserInDB,
        test_user2: UserInDB,
        test_qso_created: QsoInDB,
        db: Database) -> None:

        users = (test_user2, None)

        user = users[value] if attr == "user" else test_user
        qso_id = value if attr == "qso_id" else test_qso_created.id
        
        client = create_authorized_client(user=user)

        res = await client.delete(app.url_path_for("qso:delete-qso", 
            qso_id=qso_id)) 

        assert res.status_code == status_code

        if status_code != 404:
            qso_repo = QsoRepository(db)
            qso_in_db = await qso_repo.get_qso_by_id(id=qso_id)
            if status_code == 200:
                assert qso_in_db is None
            else:
                assert qso_in_db

class TestQsoUpdate:
    
    @pytest.mark.parametrize(
        "attr, value, status_code, comments",
        (
            (None, None, 200, "ok"),
            ("user", 0, 403, "wrong user"),
            ("user", 1, 401, "unauthenticated"),
            ("qso_id", 18, 404, "nonexistent qso"),
            ("params", {"callsign": "ADM1N/QRP/M/M"}, 200, "ok callsign"),
            ("params", {"callsign": "bad callsign"}, 422, "bad callsign"),
            ("qso_id", 18, 404, "nonexistent qso"),
        ),
    )
    async def test_update_qso(self, *,
        app: FastAPI, 
        create_authorized_client: Callable,
        attr: str,
        value: str,
        status_code: int,
        comments: str,
        test_user: UserInDB,
        test_user2: UserInDB,
        test_qso_created: QsoInDB,
        test_qso_params: dict,
        db: Database) -> None:

        users = (test_user2, None)
        upd_params = {
            "callsign": "ADM1N/QRP/M",
            "qso_datetime": "2022-11-08T08:55:17.532Z",
            "band": "80M",
            "freq": 9000.59,
            "qso_mode": "SSB",
            "rst_s": 699,
            "rst_r": 699,
            "name": "some other name",
            "qth": "some other city",
            "gridsquare": "bb11aa",
            "extra": {"foo": "foobar"}
        }

        user = users[value] if attr == "user" else test_user
        qso_id = value if attr == "qso_id" else test_qso_created.id
        if attr == "params":
            upd_params = value

        
        client = create_authorized_client(user=user)

        res = await client.put(app.url_path_for("qso:update-qso", qso_id=qso_id), 
                json={"qso_update": upd_params})

        assert res.status_code == status_code

        if status_code != 404:
            qso_repo = QsoRepository(db)
            qso_in_db = (await qso_repo.get_qso_by_id(id=qso_id)).dict()
            if status_code == 200:
                test_qso_params.update(upd_params)
            for field in upd_params:
                if field != "qso_datetime":
                    assert test_qso_params[field] == qso_in_db[field]

def cmp_qso(qso_in_db: QsoInDB, qso_dict: dict) -> None:
    qso_in_db_dict = qso_in_db.dict()
    for field in qso_dict:
        if field not in ('qso_datetime', 'updated_at', 'created_at'):
            assert str(qso_dict[field]) == str(qso_dict[field])

class TestQsoQueries:
   
    @pytest.mark.parametrize(
        "log_id, status_code",
        (
            (None, 200),
            (18, 404),
        ),
    )
    async def test_query_by_log_id(self, *,
        app: FastAPI, 
        client: TestClient,
        test_qso_created: QsoInDB,
        log_id: int,
        status_code: int,
        db: Database,
        )-> None:

        if not log_id:
            log_id = test_qso_created.log_id
        res = await client.get(app.url_path_for("qso:query-by-log", 
            log_id=log_id))

        assert res.status_code == status_code

        if status_code == 200:
            qsos = res.json()
            qso_search = [qso for qso in qsos if int(qso['id']) == test_qso_created.id]
            assert len(qso_search)
            cmp_qso(test_qso_created, qso_search[0])
 
    @pytest.mark.parametrize(
        "qso_id, status_code",
        (
            (None, 200),
            (18, 404),
        ),
    )
    async def test_query_by_id(self, *,
        app: FastAPI, 
        client: TestClient,
        test_qso_created: QsoInDB,
        qso_id: int,
        status_code: int,
        db: Database,
        )-> None:

        if not qso_id:
            qso_id = test_qso_created.id
        res = await client.get(app.url_path_for("qso:query-by-id", 
            qso_id=qso_id))

        assert res.status_code == status_code

        if status_code == 200:
            cmp_qso(test_qso_created, res.json())

