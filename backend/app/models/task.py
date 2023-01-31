from typing import Any
from pydantic import BaseModel
from enum import StrEnum

from app.models.core import IDStrModelMixin, CoreModel

class TaskStatus(StrEnum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    RETRY = "RETRY"
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"
    
class TaskBase(CoreModel, IDStrModelMixin):
    pass

class TaskResult(TaskBase):
    status: TaskStatus
    result: Any


