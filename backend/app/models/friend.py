from app.models.core import IDModelMixin, CoreModel

class FriendBase(CoreModel):
    """
        Is used for create/delete queries
    """
    friend_id: int


class FriendInDB(IDModelMixin, FriendBase):
    """
    Add in id, user_id
    """
    user_id: int

class FriendPublic(CoreModel):
    """ 
    Convert ids to str for json dump
    """
    id: str
    user_id: str
    friend_id: str
