from pydantic import BaseModel

import uuid

class User(BaseModel):
    id: uuid.UUID
    name: str
