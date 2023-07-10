from pydantic import BaseModel

import uuid

class User(BaseModel):
    id: uuid.UUID
    name: str

class NewUser(BaseModel):
    username: str
    phone: str
    company: str
    password: str