from typing import Optional, List
from enum import IntEnum

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel
from app.models.media import MediaPublic

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

class PostUpdate(PostBase):
    post_images: List[int]
    deleted_images: List[int]

class PostInDB(PostBase, IDModelMixin, DateTimeModelMixin):
    user_id: int
    images: Optional[List[MediaPublic]]

class PostPublic(PostInDB):
    id: str
    user_id: str
    images: Optional[List[MediaPublic]]


