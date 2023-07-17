from pydantic import BaseModel

import uuid

class User(BaseModel):
    id: uuid.UUID
    name: str

class NewUser(BaseModel):
    username: str
    phone: str='79115901599'
    company: str
    password: str