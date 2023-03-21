from typing import Optional
from enum import IntEnum

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel

class PostType(IntEnum):
    user = 0
    site = 1

class PostVisibility(IntEnum):
    private = 0
    friends = 1
    logged_users = 2
    everybody = 3

class PostBase(CoreModel):
    post_type: Optional[PostType]
    visibility: Optional[PostVisibility]
    title: Optional[str]
    contents: Optional[str]

class PostInDB(PostBase, IDModelMixin, DateTimeModelMixin):
    user_id: int

class PostPublic(PostInDB):
    id: str
    user_id: str


