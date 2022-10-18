from typing import Optional
from enum import Enum

from app.models.core import IDModelMixin, CoreModel


class UserBase(CoreModel):
    """
    All common characteristics of our User resource
    """
    email: str


class UserCreate(UserBase):
    email: str
    password: str


class UserUpdate(UserBase):
    email_verified: Optional[bool]
    password: Optional[str]


class UserInDB(IDModelMixin, UserBase):
    email_verified: bool

