from typing import List, Optional

import logging

from pydantic import constr
from fastapi import Depends, APIRouter, HTTPException, Path, Body, Form, status, UploadFile, File
from fastapi.responses import StreamingResponse
from starlette.status import (
        HTTP_400_BAD_REQUEST, 
        HTTP_401_UNAUTHORIZED, 
        HTTP_404_NOT_FOUND )

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.qso_logs import get_qso_log_for_update
from app.api.dependencies.qso import get_qso_for_update
from app.models.qso_log import QsoLogInDB
from app.models.qso import QsoBase, QsoInDB, QsoUpdate, QsoPublic, Band, QsoMode, QsoFilter
from app.models.user import UserInDB
from app.models.core import FullCallsign
from app.db.repositories.qso import QsoRepository, DuplicateQsoError  
from app.db.repositories.qso_logs import QsoLogsRepository
from app.utils.adif import create_adif

import logging

router = APIRouter()

async def write_qso(*, qso_repo: QsoRepository, 
        log_id: int = None,
        qso: QsoBase,
        qso_update: QsoUpdate = None) -> QsoPublic:

    try:
        qso_from_db = (await qso_repo.update_qso(qso=qso, qso_update=qso_update) if qso_update
                else await qso_repo.create_qso(new_qso=qso, log_id=log_id))
        return QsoPublic(**qso_from_db.dict())
    except DuplicateQsoError:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="The QSO is already in this log."
        )

@router.post("/logs/{log_id}", response_model=QsoPublic, name="qso:create-qso")
async def create_qso(*,
    log_id: int,
    new_qso: QsoBase = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
    qso_log: QsoLogInDB = Depends(get_qso_log_for_update),
    qso_repo: QsoRepository = Depends(get_repository(QsoRepository)),    
) -> QsoPublic:

    return await write_qso(qso_repo=qso_repo, qso=new_qso, log_id=log_id)

@router.delete("/{qso_id}", response_model=dict, name="qso:delete-qso")
async def delete_qso(*,
    qso_id: int,
	current_user: UserInDB = Depends(get_current_active_user),
	qso_repo: QsoRepository = Depends(get_repository(QsoRepository)),    
    qso_log: QsoInDB = Depends(get_qso_for_update)
) -> dict:

    await qso_repo.delete_qso(id=qso_id)

    return {"result": "Ok"}

@router.put("/{qso_id}", response_model=QsoPublic, name="qso:update-qso")
async def update_qso(*,
    qso_update: QsoUpdate = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
	qso_repo: QsoRepository = Depends(get_repository(QsoRepository)),    
    qso: QsoInDB = Depends(get_qso_for_update)
) -> QsoPublic:

    return await write_qso(qso_repo=qso_repo, qso=qso, qso_update=qso_update)

@router.get("/logs/{log_id}/qso", response_model=List[QsoPublic], name="qso:query-by-log")
async def qso_query_by_log(*,
    log_id: int,
	qso_repo: QsoRepository = Depends(get_repository(QsoRepository)),
    callsign_search: Optional[constr(to_upper=True, min_length=2)] = None,
    band: Optional[Band] = None,
    qso_mode: Optional[QsoMode] = None, 
    limit: Optional[int] = 50,
    offset: Optional[int] = None
) -> List[QsoPublic]:

    if callsign_search:
        callsign_search = callsign_search.replace('*', '%')
        logging.warning(callsign_search)
    qso = await qso_repo.get_qso_by_log_id(
            log_id=log_id, 
            callsign_search=callsign_search, 
            band=band, 
            qso_mode=qso_mode,
            limit=limit,
            offset=offset)

    if not qso:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Qso not found"
        )

    return [QsoPublic(**qso.dict()) for qso in qso]

@router.get("/logs/{log_id}/callsigns/{callsign_start}", 
        response_model=List[FullCallsign], name="qso:query-callsigns-by-log")
async def callsigns_query_by_log(*,
    log_id: int,
    callsign_start: constr(to_upper=True),
    limit: int = 20,
	qso_repo: QsoRepository = Depends(get_repository(QsoRepository)),
) -> List[FullCallsign]:

    callsigns = await qso_repo.get_callsigns_by_log_id(log_id=log_id, callsign_start=callsign_start, limit=limit)

    if not callsigns:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Callsigns not found"
        )

    return callsigns

@router.post("/logs/{log_id}/adif", response_class=StreamingResponse, name="qso:export-adif")
async def adif_export(*,
    log_id: int,
    qso_filter: Optional[QsoFilter] = Body(..., embed=True),
	qso_repo: QsoRepository = Depends(get_repository(QsoRepository)),
) -> StreamingResponse:

    log_iter = qso_repo.qso_log_iterator(log_id=log_id, qso_filter=qso_filter)
    adif_iter = create_adif(log_iter)

    response = StreamingResponse(adif_iter, media_type="text/adi")
    response.headers["Content-Disposition"] = f"attachment; filename={log_id}.adi"

    return response


@router.get("/{qso_id}", response_model=QsoPublic, name="qso:query-by-id")
async def qso_by_id(*,
    qso_id: int,
	qso_repo: QsoRepository = Depends(get_repository(QsoRepository)),    
) -> List[QsoPublic]:

    qso = await qso_repo.get_qso_by_id(id=qso_id)

    if not qso:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Qso not found"
        )

    return QsoPublic(**qso.dict())


