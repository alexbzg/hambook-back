from fastapi import Depends, HTTPException, status

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user
from app.db.repositories.qso_logs import QsoLogsRepository
from app.models.qso_log import QsoLogInDB
from app.models.user import UserInDB


async def get_qso_log_for_update(log_id: int, 
	current_user: UserInDB = Depends(get_current_active_user),
    qso_logs_repo: QsoLogsRepository = Depends(get_repository(QsoLogsRepository))) -> QsoLogInDB:

    log = await qso_logs_repo.get_log_by_id(id=log_id)

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

    return log

