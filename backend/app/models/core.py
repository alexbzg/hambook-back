from typing import Optional
from datetime import datetime
from pydantic import BaseModel, validator, constr

Callsign = constr(regex=r"[a-zA-Z]{1,4}\d{1,3}[a-zA-Z]{1,4}")

class CoreModel(BaseModel):
    """
    Any common logic to be shared by all models goes here.
    """
    pass

class DateTimeModelMixin(BaseModel):
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @validator("created_at", "updated_at", pre=True)
    def default_datetime(cls, value: datetime) -> datetime:
        return value or datetime.now()

class IDModelMixin(BaseModel):
    id: int

