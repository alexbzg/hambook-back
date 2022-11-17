from typing import Optional
import uuid
import os
import os.path

import aiofiles

from app.models.core import FileType
from app.models.media import MediaType
from app.core.config import STATIC_WWW_ROOT

def get_directory(*,
    file_type: FileType,
    media_type: Optional[MediaType]) -> str:
    if file_type == FileType.media:
        if media_type == MediaType.avatar:
            return 'media/avatars'
        return 'media'
    return ''

def create_path(*,
    file_type: FileType,
    media_type: Optional[MediaType],
    name: Optional[str],
    ext: Optional[str]) -> str:
    dir = self.get_directory(file_type=file_type, media_type=media_type)
    if not name:
        name = str(uuid.uuid4())
    if ext:
        name += f".{ext}"
    return os.path.join(dir, name)

def full_path(path: str):
    return os.path.join(STATIC_WWW_ROOT, path)

def delete_file(path: str) -> None:
    path = full_path(path)
    if os.path.isfile(full_path):
        os.unlink(full_path)

def open_file(path: str, mode: str) -> aiofiles.base.AiofilesContextManager:
    path = full_path(path)
    return aiofiles.open(path, mode)

    


