from fastapi import Depends, HTTPException, status

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user
from app.db.repositories.qso_logs import QsoLogsRepository
from app.db.repositories.qso import QsoRepository
from app.models.qso import QsoInDB
from app.models.user import UserInDB

async def get_qso_for_update(qso_id: int, 
	current_user: UserInDB = Depends(get_current_active_user),
    qso_repo: QsoRepository = Depends(get_repository(QsoRepository)),
    qso_logs_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository))) -> QsoInDB:

    qso = await qso_repo.get_qso_by_id(id=qso_id)

    if not qso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Qso not found"
        )

    log = await qso_logs_repo.get_log_by_id(id=qso.log_id)

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Qso log not found"
        )

    if int(log.user_id) != int(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    return qso

