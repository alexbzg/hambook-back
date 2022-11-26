from typing import List

from fastapi import Depends, APIRouter, HTTPException, Path, Body, Form, status, UploadFile, File
from starlette.status import (
        HTTP_400_BAD_REQUEST, 
        HTTP_401_UNAUTHORIZED, 
        HTTP_404_NOT_FOUND )
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.models.qso_log import QsoLogBase, QsoLogInDB, QsoLogPublic, QsoLogUpdate
from app.models.user import UserInDB
from app.db.repositories.qso_logs import QsoLogsRepository

import logging

router = APIRouter()

@router.post("/", response_model=QsoLogPublic, name="qso-logs:create-log")
async def create_qso_log(*,
    new_log: QsoLogBase = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
	qso_logs_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository)),    
) -> QsoLogPublic:

    created_log = await qso_logs_repo.create_qso_log(new_log=new_log)

    return QsoLogPublic(**created_log)

@router.delete("/{log_id}", response_model=dict, name="qso-logs:delete-log")
async def delete_qso_log(*,
    log_id: int,
	current_user: UserInDB = Depends(get_current_active_user),
	qso_logs_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository)),    
) -> dict:

    log_record = await qso_logs_repo.get_log_by_id(id=log_id)

    if not log_record:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Qso log not found"
        )

    if int(log_record.user_id) != int(current_user.id):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    await qso_logs_repo.delete_log(id=log_id)

    return {"result": "Ok"}

@router.put("/", response_model=QsoLogPublic, name="qso-logs:update-log")
async def update_qso_log(*,
    log_update: QsoLogUpdate = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
	qso_log_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository)),    
) -> QsoLogPublic:

    log_record = await qso_logs_repo.get_log_by_id(id=log_update.id)

    if not log_record:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Qso log not found"
        )

    if int(log_record.user_id) != int(current_user.id):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authorized",
            headers={"WWW-Authenticate": "Bearer"},
        )


    updated_log = await qso_logs_repo.update_log(log_update=log_update)

    return QsoLogPublic(**updated_log)


@router.get("/{user_id}", response_model=List[QsoLogPublic], name="qso-logs:query-by-user")
async def media_query(*,
    user_id: int,
	qso_log_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository)),    
) -> List[QsoLogPublic]:

    logs = await qso_log_repo.get_log_by_user_id(user_id=user_id)

    if not logs:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Qso logs not found"
        )

    return [QsoLogPublicFromDB(record) for log in logs]

@router.get("/", response_model=QsoLogPublic, name="qso-logs:query-by-log-id")
async def media_query(*,
    log_id: int,
	qso_log_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository)),    
) -> List[QsoLogPublic]:

    log = await qso_log_repo.get_log_by_id(id=log_id)

    if not log:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Qso log not found"
        )

    return QsoLogPublicFromDB(log)


