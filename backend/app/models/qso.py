from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel

class QsoLogBase(CoreModel):
    user_id: int
    desc: str

class QsoLogDelete(IDModelMixin):
    """
    Allow users to delete their logs
    """
    pass

class QsoLogInDB(IDModelMixin, DateTimeModelMixin, QsoLogBase):
    pass

