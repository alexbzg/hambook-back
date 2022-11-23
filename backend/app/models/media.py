from typing import Optional
from enum import IntEnum

from fastapi import UploadFile
from pydantic import root_validator, HttpUrl

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel

class MediaType(IntEnum):
    avatar = 1
    profile_media = 2

class MediaBase(CoreModel):
    user_id: int
    media_type: MediaType

class MediaUpload(MediaBase):
    """
    Required fields are user_id, media_type and uploaded file
    """
    file: UploadFile

    @root_validator
    def check_media_type(cls, values):
        if values.get('media_type') == 1:
            file_upload = values.get('file')
            if file_upload.content_type not in ('image/jpeg', 'image/png'):
                raise ValueError('Invalid file type')
        return values 

class MediaCreate(MediaBase):
    file_path: str

class MediaDelete(IDModelMixin):
    """
    Allow users to delete their media 
    """
    pass

class MediaInDB(IDModelMixin, DateTimeModelMixin, MediaCreate):
    pass

class MediaPublic(IDModelMixin, DateTimeModelMixin, MediaBase):
    user_id: str
    url: HttpUrl


