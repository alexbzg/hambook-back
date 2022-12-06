from typing import List

from app.db.repositories.base import BaseRepository
from app.models.qso import QsoBase, QsoInDB, QsoUpdate
from app.models.user import UserInDB

CREATE_QSO_QUERY = """
    INSERT INTO qso (log_id, callsign, qso_datetime, band, freq, qso_mode, 
        rst_s, rst_r, name, qth, gridsquare, extra)
    VALUES (:log_id, :callsign, :qso_datetime, :band, :freq, :qso_mode, 
        :rst_s, :rst_r, :name, :qth, :gridsquare, :extra)
    RETURNING id, log_id, callsign, qso_datetime, band, freq, qso_mode, 
        st_s, rst_r, name, qth, gridsquare, extra;
"""

UPDATE_QSO_LOG_QUERY = """
    UPDATE qso 
    SET 
        callsign = :callsign, 
        qso_datetime = :qso_datetime, 
        band = :band,
        freq = :freq, 
        qso_mode = :qso_mode, 
        rst_s = :rst_s, 
        rst_r = :rst_r, 
        name = :nqme, 
        qth = :qth, 
        gridsquare = :gridsquare, 
        extra = :extra
    WHERE
        id = :id
    RETURNING id, log_id, callsign, qso_datetime, band, freq, qso_mode, 
        st_s, rst_r, name, qth, gridsquare, extra;
"""


DELETE_QSO_LOG_QUERY = """
    DELETE from qso
    WHERE id = :id;
"""

GET_QSO_BY_LOG_ID_QUERY = """
    SELECT id, log_id, callsign, qso_datetime, band, freq, qso_mode, 
        st_s, rst_r, name, qth, gridsquare, extra
    FROM qso
    WHERE log_id = :log_id
"""

GET_QSO_BY_ID_QUERY = """
    SELECT id, log_id, callsign, qso_datetime, band, freq, qso_mode, 
        st_s, rst_r, name, qth, gridsquare, extra
    FROM qso
    WHERE id = :id
"""


class QsoRepository(BaseRepository):

    async def create_qso(self, *, 
        new_qso: QsoBase,
        log_id: int) -> QsoInDB:

        created_qso = await self.db.fetch_one(query=CREATE_QSO_QUERY, 
                values={**new_qso.dict(), "log_id": log_id})

        return QsoInDB(**created_qso)

    async def get_qso_by_log_id(self, *, log_id: int) -> List[QsoInDB]:
        qsos = await self.db.fetch_all(query=GET_QSO_BY_LOG_ID_QUERY, values={"log_id": log_id})

        if not qso_logs:
            return None

        return [QsoInDB(**qso_log) for qso in qsos]

    async def get_qso_by_id(self, *, id: int) -> QsoInDB:
        qso = await self.db.fetch_one(query=GET_QSO_BY_ID_QUERY, 
                values={"id": id})

        if not qso:
            return None

        return QsoInDB(**qso)


    async def update_qso(self, *, qso: QsoInDB, qso_update: QsoBase) -> QsoInDB:

        update_params = qso.copy(update=qso_update.dict(exclude_unset=True))
        updated_qso = await self.db.fetch_one(
            query=UPDATE_QSO_QUERY,
            values=update_params.dict(
                exclude={"log_id", "created_at", "updated_at"}),
        )

        return QsoInDB(**updated_qso)


    async def delete_qso(self, *, id: int) -> None:
        await self.db.execute(query=DELETE_QSO_QUERY, values={"id": id})

