from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from app.models.task import TaskBase, TaskResult
from app.celery.worker import task_test, get_task_status


router = APIRouter()

@router.get("/")
async def test() -> dict:
    return {'status': 'Ok'}

@router.post("/task", status_code=201, response_model=TaskBase)
def test_task(delay: int = Body(..., embed=True)):
    task = task_test.delay(delay=delay)
    return TaskBase(id=task.id)


