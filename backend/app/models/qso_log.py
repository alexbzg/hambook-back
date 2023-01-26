from typing import Optional, List
from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel, FullCallsign
from app.models.qso import QsoExtraField

class QsoLogBase(CoreModel):
    """
    Used for create/update log requests also as user_id is passed through auth header
    """
    callsign: Optional[FullCallsign]
    description: Optional[str]
    extra_fields: Optional[List[QsoExtraField]]

class QsoLogInDB(IDModelMixin, DateTimeModelMixin, QsoLogBase):
    user_id: int
    qso_count: Optional[int]

class QsoLogPublic(QsoLogInDB):
    id: str
    user_id: str
