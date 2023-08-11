from pydantic import BaseModel

from config import DEFAULT_PHONE

class NewUser(BaseModel):
    username: str=None
    phone: str=DEFAULT_PHONE
    company: str
    password: str