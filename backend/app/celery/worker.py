import time

from celery import Celery
from celery.result import AsyncResult
from app.core.config import RABBITMQ_URL, DATABASE_URL
from app.models.task import TaskResult

celery_app = Celery(__name__)
celery_app.conf.broker_url = RABBITMQ_URL
celery_app.conf.result_backend = f"db+{DATABASE_URL}"

@celery_app.task(name="test")
def task_test(*, delay: int) -> bool:
    time.sleep(delay*10)
    return True

def get_task_status(task_id: str) -> TaskResult:
    task_result = AsyncResult(task_id, app=celery_app)
    result = (str(task_result.result) if isinstance(task_result.result, Exception) 
            else task_result.result)
    return TaskResult(id=task_id, status=task_result.status, result=result) 

