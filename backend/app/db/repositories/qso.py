from typing import List
import logging
from PIL import Image

from app.db.repositories.base import BaseRepository
from app.models.qso import QsoLogCreate, QsoLogInDB
from app.models.user import UserInDB

CREATE_QSO_LOG_QUERY = """
    INSERT INTO qso_logs (desc, user_id)
    VALUES (:desc, :user_id)
    RETURNING id, desc, user_id;
"""

DELETE_MEDIA_QUERY = """
    DELETE from qso_logs
    WHERE id = :id;
"""

GET_QSO_LOGS_BY_USER_ID_QUERY = """
    SELECT id, desc, user_id
    FROM qso_logs
    WHERE user_id = :user_id;
"""

GET_QSO_LOG_BY_ID_QUERY = """
    SELECT id, desc, user_id
    FROM qso_log
    WHERE id = :id;
"""

class MediaRepository(BaseRepository):

    async def create_qso_log(self, *, qso_log_create: QsoLogCreate) -> QsoLogInDB:

        created_log = await self.db.fetch_one(query=CREATE_QSO_LOG_QUERY, 
                values=qso_log_create.dict())

        return QsoLogInDB(**created_log)

    async def get_qso_log_by_user_id(self, *, user_id: int) -> List[MediaInDB]:
        qso_logs = await self.db.fetch_all(query=GET_QSO_LOGS_BY_USER_ID, values={"user_id": user_id})

        if not qso_logs:
            return None

        return [QsoLogInDB(**qso_log) for qso_log in qso_logs]

    async def get_qso_log_by_id(self, *, id: int) -> MediaInDB:
        qso_log = await self.db.fetch_one(query=GET_QSO_LOG_BY_ID_QUERY, 
                values={"id": id})

        if not qso_log:
            return None

        return QsoLogInDB(**qso_log)


    async def delete_qso_log(self, *, id: int) -> None:
        await self.db.execute(query=DELETE_QSO_LOG_QUERY, values={"id": id})

