import uuid

from pydantic import BaseModel

from config import DEFAULT_PHONE
from payment.schemas import UserAccess
from utils import BaseResponse


class NewUser(BaseModel):
    username: str=None
    phone: str=DEFAULT_PHONE
    company: str
    password: str

class UserProfile(BaseModel):
    id: uuid.UUID
    username: str
    company: str | None
    theme: str
    access: UserAccess

class UserProfileResponse(BaseResponse):
    data: UserProfile

class Theme(BaseModel):
    theme: str

class Username(BaseModel):
    username: str