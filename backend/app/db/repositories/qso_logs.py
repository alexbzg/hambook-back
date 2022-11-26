from typing import List

from app.db.repositories.base import BaseRepository
from app.models.qso_log import QsoLogBase, QsoLogInDB, QsoLogUpdate
from app.models.user import UserInDB

CREATE_QSO_LOG_QUERY = """
    INSERT INTO qso_logs (callsign, desc, user_id)
    VALUES (:callsign, :desc, :user_id)
    RETURNING id, callsign, desc, user_id;
"""

UPDATE_QSO_LOG_QUERY = """
    UPDATE qso_logs
    set 
        desc = :desc, 
        callsign = :callsign
    WHERE id = :id
    RETURNING id, callsign, desc, user_id;
"""


DELETE_MEDIA_QUERY = """
    DELETE from qso_logs
    WHERE id = :id;
"""

GET_QSO_LOGS_BY_USER_ID_QUERY = """
    SELECT id, callsign, desc, user_id
    FROM qso_logs
    WHERE user_id = :user_id;
"""

GET_QSO_LOG_BY_ID_QUERY = """
    SELECT id, callsign, desc, user_id
    FROM qso_log
    WHERE id = :id;
"""

class QsoLogsRepository(BaseRepository):

    async def create_log(self, *, new_log: QsoLogBase) -> QsoLogInDB:

        created_log = await self.db.fetch_one(query=CREATE_QSO_LOG_QUERY, 
                values=new_log.dict())

        return QsoLogInDB(**created_log)

    async def get_logs_by_user_id(self, *, user_id: int) -> List[QsoLogInDB]:
        qso_logs = await self.db.fetch_all(query=GET_QSO_LOGS_BY_USER_ID, values={"user_id": user_id})

        if not qso_logs:
            return None

        return [QsoLogInDB(**qso_log) for qso_log in qso_logs]

    async def get_log_by_id(self, *, id: int) -> QsoLogInDB:
        qso_log = await self.db.fetch_one(query=GET_QSO_LOG_BY_ID_QUERY, 
                values={"id": id})

        if not qso_log:
            return None

        return QsoLogInDB(**qso_log)

    async def update_log(self, *, log_update: QsoLogUpdate) -> QsoLogInDB:
        qso_log = await self.db.fetch_one(query=GET_QSO_LOG_BY_ID_QUERY, 
                values={"id": log_update.id})

        if not qso_log:
            return None

        update_params = qso_log.copy(update=log_update.dict(exclude_unset=True))
        updated_qso_log = await self.db.fetch_one(
            query=UPDATE_QSO_LOG_QUERY,
            values=update_params.dict(
                exclude={"user_id", "created_at", "updated_at"}),
        )

        return QsoLogInDB(**updated_qso_log)


    async def delete_log(self, *, id: int) -> None:
        await self.db.execute(query=DELETE_QSO_LOG_QUERY, values={"id": id})

