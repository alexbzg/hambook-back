from typing import List

from app.db.repositories.base import BaseRepository
from app.models.qso_log import QsoLogBase, QsoLogInDB
from app.models.user import UserInDB

CREATE_QSO_LOG_QUERY = """
    INSERT INTO qso_logs (callsign,  description, user_id)
    VALUES (:callsign, :description, :user_id)
    RETURNING id, callsign, description, user_id, extra_fields;
"""

UPDATE_QSO_LOG_QUERY = """
    UPDATE qso_logs
    set 
        description = :description, 
        callsign = :callsign,
        extra_fields = :extra_fields
    WHERE id = :id
    RETURNING id, callsign, description, user_id, extra_fields;
"""


DELETE_QSO_LOG_QUERY = """
    DELETE from qso_logs
    WHERE id = :id;
"""

GET_QSO_LOGS_BY_USER_ID_QUERY = """
    SELECT id, callsign, description, user_id, extra_fields,
       (SELECT count(*) from qso 
            WHERE log_id = qso_logs.id) as qso_count
    FROM qso_logs
    WHERE user_id = :user_id
    order by id;
"""

GET_QSO_LOG_BY_ID_QUERY = """
    SELECT id, callsign, description, user_id, extra_fields,
       (SELECT count(*) from qso 
            WHERE log_id = :id) as qso_count
    FROM qso_logs
    WHERE id = :id;
"""

class QsoLogsRepository(BaseRepository):

    async def create_log(self, *, 
        new_log: QsoLogBase,
        requesting_user: UserInDB) -> QsoLogInDB:

        created_log = await self.db.fetch_one(query=CREATE_QSO_LOG_QUERY, 
                values={**new_log.dict(), "user_id": int(requesting_user.id)})

        return QsoLogInDB(**created_log)

    async def get_logs_by_user_id(self, *, user_id: int) -> List[QsoLogInDB]:
        qso_logs = await self.db.fetch_all(query=GET_QSO_LOGS_BY_USER_ID_QUERY, values={"user_id": user_id})

        if not qso_logs:
            return None

        return [QsoLogInDB(**qso_log) for qso_log in qso_logs]

    async def get_log_by_id(self, *, id: int) -> QsoLogInDB:
        qso_log = await self.db.fetch_one(query=GET_QSO_LOG_BY_ID_QUERY, 
                values={"id": id})

        if not qso_log:
            return None

        return QsoLogInDB(**qso_log)


    async def update_log(self, *, log: QsoLogInDB, log_update: QsoLogBase) -> QsoLogInDB:

        update_params = log.copy(update=log_update.dict(exclude_unset=True))
        updated_qso_log = await self.db.fetch_one(
            query=UPDATE_QSO_LOG_QUERY,
            values=update_params.dict(
                exclude={"user_id", "qso_count", "created_at", "updated_at"}),
        )

        return QsoLogInDB(**updated_qso_log)


    async def delete_log(self, *, id: int) -> None:
        await self.db.execute(query=DELETE_QSO_LOG_QUERY, values={"id": id})

