from typing import List, Optional, AsyncIterator
import json
from datetime import date
import logging

from pydantic import constr
from asyncpg.exceptions._base import UnknownPostgresError

from app.db.repositories.base import BaseRepository
from app.models.qso import QsoBase, QsoInDB, QsoUpdate, Band, QsoMode, QsoFilter
from app.models.core import FullCallsign
from app.models.user import UserInDB

CREATE_QSO_QUERY = """
    INSERT INTO qso (log_id, callsign, station_callsign, qso_datetime, band, freq, qso_mode, 
        rst_s, rst_r, extra)
    VALUES (:log_id, :callsign, :station_callsign, :qso_datetime, :band, :freq, :qso_mode, 
        :rst_s, :rst_r, :extra)
    RETURNING id, log_id, callsign, station_callsign, qso_datetime, band, freq, qso_mode, 
        rst_s, rst_r, extra, created_at, updated_at;
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
        extra = :extra
    WHERE
        id = :id
    RETURNING id, log_id, callsign, station_callsign, qso_datetime, band, freq, qso_mode, 
        rst_s, rst_r, extra, created_at, updated_at;
"""


DELETE_QSO_QUERY = """
    DELETE from qso
    WHERE id = :id;
"""

GET_QSO_BY_LOG_ID_QUERY = """
    SELECT id, log_id, callsign, station_callsign, qso_datetime, band, freq, qso_mode, 
        rst_s, rst_r, extra, created_at, updated_at
    FROM qso
    WHERE log_id = :log_id and 
        (cast(:callsign_search as text) is null or callsign like :callsign_search) and 
        (cast(:band as text) is null or band = :band) and
        (cast(:qso_mode as text) is null or :qso_mode = qso_mode) and
        (cast(:date_begin as timestamp) is null or :date_begin < qso_datetime) and
        (cast(:date_end as timestamp) is null or :date_end + interval '1 day' > qso_datetime)
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
        rst_s, rst_r, extra, created_at, updated_at
    FROM qso
    WHERE id = :id;
"""

class DuplicateQsoError(Exception):
    pass

class QsoRepository(BaseRepository):

    async def write_qso(self, *, query: str, values: dict):
        try: 
            return await self.db.fetch_one(
                    query=query, 
                    values=values)
        except UnknownPostgresError as exc:
            if str(exc) == 'The QSO is already in this log.':
                raise DuplicateQsoError()

    async def create_qso(self, *, 
        new_qso: QsoBase,
        log_id: int) -> QsoInDB:

        created_qso = await self.write_qso(
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
        qso_mode: Optional[QsoMode] = None,
        date_begin: Optional[date] = None,
        date_end: Optional[date] = None ) -> List[QsoInDB]:
        qsos = await self.db.fetch_all(query=GET_QSO_BY_LOG_ID_QUERY, 
                values={
                    "log_id": log_id,
                    "callsign_search": callsign_search,
                    "band": band,
                    "qso_mode": qso_mode,
                    "date_begin": date_begin,
                    "date_end": date_end
                    })

        if not qsos:
            return None

        return [QsoInDB(**qso) for qso in qsos]

    async def qso_log_iterator(self, *,
        log_id: int,
        qso_filter: QsoFilter) -> AsyncIterator[QsoInDB]:
        async for qso in self.db.iterate(query=GET_QSO_BY_LOG_ID_QUERY, 
                values={
                    "log_id": log_id,
                    "callsign_search": qso_filter.callsign_search,
                    "band": qso_filter.band,
                    "qso_mode": qso_filter.qso_mode,
                    "date_begin": qso_filter.date_begin,
                    "date_end": qso_filter.date_end
                    }):
            yield QsoInDB(**qso)

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

        updated_qso = await self.write_qso(
            query=UPDATE_QSO_QUERY,
            values=update_params
        )

        return QsoInDB(**updated_qso)


    async def delete_qso(self, *, id: int) -> None:
        await self.db.execute(query=DELETE_QSO_QUERY, values={"id": id})

