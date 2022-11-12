from typing import Optional
from datetime import date

from pydantic import EmailStr, HttpUrl

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel, Callsign


class ProfileBase(CoreModel):
    full_name: Optional[str]
    address: Optional[str]
    default_image: Optional[str]
    current_callsign: Optional[Callsign]
    prev_callsigns: Optional[str]
    birthdate: Optional[date]
    bio: Optional[str]

class ProfileCreate(ProfileBase):
    """
    The only field required to create a profile is the users id
    """
    user_id: int


class ProfileUpdate(ProfileBase):
    """
    Allow users to update any or no fields, as long as it's not user_id
    """
    pass


class ProfileInDB(IDModelMixin, DateTimeModelMixin, ProfileBase):
    user_id: int
    email: Optional[EmailStr]

class ProfilePublic(ProfileInDB):
    pass

