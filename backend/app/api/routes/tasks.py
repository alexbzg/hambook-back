from fastapi import APIRouter

from app.models.task import TaskResult
from app.celery.worker import get_task_status


router = APIRouter()

@router.get("/{task_id}", response_model=TaskResult)
def get_status(task_id: str):
    return get_task_status(task_id)

