from typing import List

from fastapi import Depends, APIRouter, HTTPException, Path, Body, Form, status, UploadFile, File
from starlette.status import (
        HTTP_400_BAD_REQUEST, 
        HTTP_401_UNAUTHORIZED, 
        HTTP_404_NOT_FOUND )
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.qso_logs import get_qso_log_for_update
from app.models.qso_log import QsoLogBase, QsoLogInDB, QsoLogPublic
from app.models.user import UserInDB
from app.models.core import FileType
from app.models.task import TaskBase
from app.services.static_files import save_file, full_path
from app.celery.worker import task_adif_import
from app.db.repositories.qso_logs import QsoLogsRepository

from app.db.repositories.qso import QsoRepository
from app.utils.adif import parse_adif

import logging

router = APIRouter()

@router.post("/", response_model=QsoLogPublic, name="qso-logs:create-log")
async def create_qso_log(*,
    new_log: QsoLogBase = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
	qso_logs_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository)),    
) -> QsoLogPublic:

    created_log = await qso_logs_repo.create_log(new_log=new_log, requesting_user=current_user)

    return QsoLogPublic(**created_log.dict())

@router.delete("/{log_id}", response_model=dict, name="qso-logs:delete-log")
async def delete_qso_log(*,
    log_id: int,
	current_user: UserInDB = Depends(get_current_active_user),
	qso_logs_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository)),    
    qso_log: QsoLogInDB = Depends(get_qso_log_for_update)
) -> dict:

    await qso_logs_repo.delete_log(id=log_id)

    return {"result": "Ok"}

@router.put("/{log_id}", response_model=QsoLogPublic, name="qso-logs:update-log")
async def update_qso_log(*,
    log_update: QsoLogBase = Body(..., embed=True),
	current_user: UserInDB = Depends(get_current_active_user),
	qso_logs_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository)),    
    qso_log: QsoLogInDB = Depends(get_qso_log_for_update)
) -> QsoLogPublic:

    updated_log = await qso_logs_repo.update_log(log=qso_log, log_update=log_update)

    return QsoLogPublic(**updated_log.dict())

@router.put("/{log_id}/adif", response_model=TaskBase, name="qso-logs:adif-import")
async def adif_import(*,
	current_user: UserInDB = Depends(get_current_active_user),
	qso_logs_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository)),    
    qso_repo: QsoRepository = Depends(get_repository(QsoRepository)),    
    qso_log: QsoLogInDB = Depends(get_qso_log_for_update),
    file: UploadFile = File(...),
) -> TaskBase:

    file_path = full_path(await save_file(
            file_type=FileType.adi,
            upload=file))

    task = task_adif_import.delay(log=qso_log, file_path=file_path)
    return TaskBase(id=task.id)

@router.get("/", response_model=List[QsoLogPublic], name="qso-logs:query-by-user")
async def qso_logs_query_by_user(*,
    user_id: int,
	qso_logs_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository)),    
) -> List[QsoLogPublic]:

    logs = await qso_logs_repo.get_logs_by_user_id(user_id=user_id)

    if not logs:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Qso logs not found"
        )

    return [QsoLogPublic(**log.dict()) for log in logs]

@router.get("/{log_id}", response_model=QsoLogPublic, name="qso-logs:query-by-log-id")
async def qso_log_by_id(*,
    log_id: int,
	qso_logs_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository)),    
) -> List[QsoLogPublic]:

    log = await qso_logs_repo.get_log_by_id(id=log_id)

    if not log:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Qso log not found"
        )

    return QsoLogPublic(**log.dict())


