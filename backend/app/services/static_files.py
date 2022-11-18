from typing import Optional
import uuid
import os
import os.path

from fastapi import UploadFile
from pydantic import HttpUrl
import aiofiles

from app.models.core import FileType
from app.models.media import MediaType
from app.core.config import STATIC_WWW_ROOT, SRV_URI

def get_directory(*,
    file_type: FileType,
    media_type: Optional[MediaType] = None) -> str:
    if file_type == FileType.media:
        if media_type == MediaType.avatar:
            return '/media/avatars'
        return '/media'
    return '/'

def get_file_extention(content_type: str) -> str:
    if content_type == 'image/jpeg':
        return '.jpeg'
    if content_type == 'image/png':
        return '.png'
    return ''

async def save_file(*,
    file_type: FileType,
    media_type: Optional[MediaType] = None,
    name: Optional[str] = None,
    upload: UploadFile) -> str:
    path = create_path(
            file_type=file_type, 
            media_type=media_type, 
            name=name, 
            ext=get_file_extention(upload.content_type))
    async with aiofiles.open(full_path(path), 'wb') as out_file:
        while content := await upload.read(1024):  
            await out_file.write(content)
    return path

def create_path(*,
    file_type: FileType,
    media_type: Optional[MediaType] = None,
    name: Optional[str] = None,
    ext: Optional[str] = None) -> str:
    dir = get_directory(file_type=file_type, media_type=media_type)
    if not name:
        name = str(uuid.uuid4())
    if ext:
        name += f"{ext}"
    return os.path.join(dir, name)

def full_path(path: str):
    return f"{STATIC_WWW_ROOT}{path}"

def delete_file(path: str) -> None:
    path = full_path(path)
    if os.path.isfile(path):
        os.unlink(path)

def open_file(path: str, mode: str) -> aiofiles.base.AiofilesContextManager:
    path = full_path(path)
    return aiofiles.open(path, mode)

def get_url_by_path(path: str) -> HttpUrl:
    return f"{SRV_URI}{path}"
    


