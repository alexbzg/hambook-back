from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel, FullCallsign

class QsoLogBase(CoreModel):
    user_id: int
    callsign: FullCallsign
    desc: str

class QsoLogUpdate(IDModelMixin, QsoLogBase):
    """
    Allow users to update their logs
    """
    pass

class QsoLogInDB(IDModelMixin, DateTimeModelMixin, QsoLogBase):
    pass


class QsoLogPublic(QsoLogInDB):
    id: str
    user_id: str
