from typing import List, Optional
import json

from pydantic import constr

from app.db.repositories.base import BaseRepository
from app.models.qso import QsoBase, QsoInDB, QsoUpdate, Band, QsoMode
from app.models.core import FullCallsign
from app.models.user import UserInDB

CREATE_QSO_QUERY = """
    INSERT INTO qso (log_id, callsign, station_callsign, qso_datetime, band, freq, qso_mode, 
        rst_s, rst_r, name, qth, gridsquare, comment, extra)
    VALUES (:log_id, :callsign, :station_callsign, :qso_datetime, :band, :freq, :qso_mode, 
        :rst_s, :rst_r, :name, :qth, :gridsquare, :comment, :extra)
    RETURNING id, log_id, callsign, station_callsign, qso_datetime, band, freq, qso_mode, 
        rst_s, rst_r, name, qth, gridsquare, comment, extra, created_at, updated_at;
"""

UPDATE_QSO_QUERY = """
    UPDATE qso 
    SET 
        callsign = :callsign, 
        station_callsign = :station_callsign, 
        qso_datetime = :qso_datetime, 
        band = :band,
        freq = :freq, 
        qso_mode = :qso_mode, 
        rst_s = :rst_s, 
        rst_r = :rst_r, 
        name = :name, 
        qth = :qth, 
        gridsquare = :gridsquare, 
        comment = :comment,
        extra = :extra
    WHERE
        id = :id
    RETURNING id, log_id, callsign, station_callsign, qso_datetime, band, freq, qso_mode, 
        rst_s, rst_r, name, qth, gridsquare, extra, comment, created_at, updated_at;
"""


DELETE_QSO_QUERY = """
    DELETE from qso
    WHERE id = :id;
"""

GET_QSO_BY_LOG_ID_QUERY = """
    SELECT id, log_id, callsign, station_callsign, qso_datetime, band, freq, qso_mode, 
        rst_s, rst_r, name, qth, gridsquare,  comment, extra, created_at, updated_at
    FROM qso
    WHERE log_id = :log_id and 
        (cast(:callsign_search as text) is null or callsign like :callsign_search) and 
        (cast(:band as text) is null or band = :band) and
        (cast(:qso_mode as text) is null or :qso_mode = qso_mode)
    order by id desc;
"""

GET_CALLSIGNS_BY_LOG_ID_QUERY = """
    SELECT distinct callsign
    FROM qso
    WHERE log_id = :log_id and callsign like :callsign_template
    order by callsign
"""



GET_QSO_BY_ID_QUERY = """
    SELECT id, log_id, callsign, station_callsign, qso_datetime, band, freq, qso_mode, 
        rst_s, rst_r, name, qth, gridsquare, comment, extra, created_at, updated_at
    FROM qso
    WHERE id = :id;
"""


class QsoRepository(BaseRepository):

    async def create_qso(self, *, 
        new_qso: QsoBase,
        log_id: int) -> QsoInDB:

        created_qso = await self.db.fetch_one(
                query=CREATE_QSO_QUERY, 
                values={
                    **new_qso.dict(exclude={"extra"}), 
                    "extra": json.dumps(new_qso.extra), 
                    "log_id": log_id
                    })


        return QsoInDB(**created_qso)

    async def get_qso_by_log_id(self, *, 
        log_id: int,
        callsign_search: Optional[str] = None,
        band: Optional[Band] = None,
        qso_mode: Optional[QsoMode] = None) -> List[QsoInDB]:
        qsos = await self.db.fetch_all(query=GET_QSO_BY_LOG_ID_QUERY, 
                values={
                    "log_id": log_id,
                    "callsign_search": callsign_search,
                    "band": band,
                    "qso_mode": qso_mode
                    })

        if not qsos:
            return None

        return [QsoInDB(**qso) for qso in qsos]

    async def get_callsigns_by_log_id(self, *, 
        log_id: int,
        callsign_start: constr(to_upper=True),
        limit: Optional[int] = 20) -> List[FullCallsign]:
        query = GET_CALLSIGNS_BY_LOG_ID_QUERY
        if limit:
            query += f" limit {limit}"
        callsigns = await self.db.fetch_all(query=query, 
                values={
                    "log_id": log_id,
                    "callsign_template": f"{callsign_start}%"
                    })
        if not callsigns:
            return None


        return [FullCallsign(callsign['callsign']) for callsign in callsigns]


    async def get_qso_by_id(self, *, id: int) -> QsoInDB:
        qso = await self.db.fetch_one(query=GET_QSO_BY_ID_QUERY, 
                values={"id": id})

        if not qso:
            return None

        return QsoInDB(**qso)


    async def update_qso(self, *, qso: QsoInDB, qso_update: QsoBase) -> QsoInDB:

        update_params = qso.copy(update=qso_update.dict(exclude_unset=True)).dict(
                exclude={"log_id", "created_at", "updated_at"})
        update_params["extra"] = json.dumps(update_params["extra"])

        updated_qso = await self.db.fetch_one(
            query=UPDATE_QSO_QUERY,
            values=update_params
        )

        return QsoInDB(**updated_qso)


    async def delete_qso(self, *, id: int) -> None:
        await self.db.execute(query=DELETE_QSO_QUERY, values={"id": id})

