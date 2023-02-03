import time
import asyncio

from celery import Celery
from celery.result import AsyncResult
from app.core.config import RABBITMQ_URL, DATABASE_URL
from app.models.task import TaskResult
from app.models.qso_log import QsoLogInDB
from app.db.tasks import connect_to_db
from app.db.repositories.qso import QsoRepository, DuplicateQsoError
from app.utils.adif import parse_adif

celery_app = Celery(__name__)
celery_app.conf.broker_url = RABBITMQ_URL
celery_app.conf.result_backend = f"db+{DATABASE_URL}"
celery_app.conf.task_serializer = "pickle"
celery_app.conf.result_serializer = "pickle"
celery_app.conf.accept_content = ["application/json", "application/x-python-serialize"]
celery_app.conf.result_accept_content = ["application/json", "application/x-python-serialize"]

@celery_app.task(name="test")
def task_test(*, delay: int) -> bool:
    time.sleep(delay*10)
    return True

def get_task_status(task_id: str) -> TaskResult:
    task_result = AsyncResult(task_id, app=celery_app)
    result = (str(task_result.result) if isinstance(task_result.result, Exception) 
            else task_result.result)
    return TaskResult(id=task_id, status=task_result.status, result=result) 

@celery_app.task(name="adif_import")
def task_adif_import(*, file_path: str, log: QsoLogInDB) -> bool:

    async def _import():
        qso_errors, qso_dupes, qso_new = [], 0, 0
        db = await connect_to_db()
        qso_repository = QsoRepository(db)
        qso_dupes, qso_new = 0, 0
        for qso in parse_adif(file_path, log_settings=log.dict(), qso_errors=qso_errors):
            try:
                await qso_repository.create_qso(new_qso=qso, log_id=log.id)
                qso_new += 1
            except DuplicateQsoError:
                qso_dupes += 1
        return {'invalid': len(qso_errors), 'duplicates': qso_dupes, 'new': qso_new}

    return asyncio.run(_import())
