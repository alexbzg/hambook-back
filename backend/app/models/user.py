from typing import Optional

from pydantic import EmailStr, constr, validator

from app.models.core import IDModelMixin, CoreModel, DateTimeModelMixin
from app.models.token import AccessToken
from app.models.profile import ProfilePublic

class UserBase(CoreModel):
    """
    All common characteristics of our User resource
    """
    email: EmailStr
    email_verified: bool = False


class UserCreate(CoreModel):
    """
        Email and password are required for registering a new user
    """
    email: EmailStr
    password: constr(min_length=8, max_length=64)


class UserPasswordUpdate(CoreModel):
    """
    Users can change their password
    """
    password: constr(min_length=8, max_length=64)
    salt: str

class UserPasswordReset(CoreModel):
    """
    Users can reset their forgotten password with token via email
    """
    password: constr(min_length=8, max_length=64)
    token: str

class UserInDB(IDModelMixin, DateTimeModelMixin, UserBase):
    """
    Add in id, created_at, updated_at, user's password and salt
    """
    password: constr(min_length=8, max_length=64)
    salt: str

class UserPublic(IDModelMixin, DateTimeModelMixin, UserBase):
    access_token: Optional[AccessToken]
    profile: Optional[ProfilePublic]
