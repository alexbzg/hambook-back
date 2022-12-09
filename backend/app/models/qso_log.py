from typing import Optional
from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel, FullCallsign

class QsoLogBase(CoreModel):
    """
    Used for create/update log requests also as user_id is passed through auth header
    """
    callsign: Optional[FullCallsign]
    description: Optional[str]

class QsoLogInDB(IDModelMixin, DateTimeModelMixin, QsoLogBase):
    user_id: int
    qso_count: Optional[int]

class QsoLogPublic(QsoLogInDB):
    id: str
    user_id: str
