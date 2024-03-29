from typing import Optional, Union, List
from datetime import date

from pydantic import HttpUrl

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel, Callsign, Phone
from app.models.media import MediaPublic

class ProfileBase(CoreModel):
    first_name: Optional[str]
    last_name: Optional[str]
    country: Optional[str]
    region: Optional[str]
    district: Optional[str]
    city: Optional[str]
    zip_code: Optional[str]
    address: Optional[str]
    phone: Optional[Phone]
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

class ProfilePublic(ProfileInDB):
    id: str
    user_id: str
    avatar: Union[MediaPublic, None]
    media: List[MediaPublic]

