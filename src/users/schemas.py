from pydantic import BaseModel

from config import DEFAULT_PHONE

import uuid

class User(BaseModel):
    id: uuid.UUID
    name: str

class NewUser(BaseModel):
    username: str=None
    phone: str=DEFAULT_PHONE
    company: str
    password: str