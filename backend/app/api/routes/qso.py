from typing import List

from fastapi import Depends, APIRouter, HTTPException, Path, Body, Form, status, UploadFile, File
from starlette.status import (
        HTTP_400_BAD_REQUEST, 
        HTTP_401_UNAUTHORIZED, 
        HTTP_404_NOT_FOUND )
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.qso_logs import get_qso_log_for_update
from app.api.dependencies.qso import get_qso_for_update
from app.models.qso_log import QsoLogInDB
from app.models.qso import QsoBase, QsoInDB, QsoUpdate, QsoPublic
from app.models.user import UserInDB
from app.db.repositories.qso import QsoRepository
from app.db.repositories.qso_logs import QsoLogsRepository

import logging

router = APIRouter()

@router.post("/logs/{log_id}", response_model=QsoPublic, name="qso:create-qso")
async def create_qso(*,
    log_id: int,
    new_qso: QsoBase = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
    qso_log: QsoLogInDB = Depends(get_qso_log_for_update)
) -> QsoPublic:

    created_qso = await qso_logs_repo.create_log(new_qso=new_log, log_id=log_id)

    return QsoPublic(**created_qso.dict())

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

    updated_qso = await qso_repo.update_qso(qso=qso, qso_update=qso_update)

    return QsoPublic(**updated_qso.dict())


@router.get("/logs/{log_id}/qso", response_model=List[QsoPublic], name="qso:query-by-log")
async def qso_query_by_log(*,
    log_id: int,
	qso_repo: QsoRepository = Depends(get_repository(QsoRepository)),    
) -> List[QsoPublic]:

    qso = await qso_repo.get_qso_by_log_id(log_id=log_id)

    if not qso:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Qso not found"
        )

    return [QsoPublic(**qso.dict()) for qso in qso]

@router.get("/{qso_id}", response_model=QsoPublic, name="qso:query-by-id")
async def qso_by_id(*,
    qso_id: int,
	qso_logs_repo: QsoLogsRepository = Depends(get_repository(QsoRepository)),    
) -> List[QsoPublic]:

    qso = await qso_repo.get_qso_by_id(id=qso_id)

    if not qso:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Qso not found"
        )

    return QsoPublic(**qso.dict())


