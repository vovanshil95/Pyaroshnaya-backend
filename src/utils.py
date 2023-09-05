import uuid
from _datetime import datetime, timedelta

from pydantic import BaseModel

def msc_now() -> datetime:
    return datetime.utcnow() + timedelta(hours=3)

class BaseResponse(BaseModel):
    message: str


class IdSchema(BaseModel):
    id: uuid.UUID

def try_uuid(s: str) -> uuid.UUID | str:
    try:
        uuid_s = uuid.UUID(hex=s)
        return uuid_s
    except ValueError:
        return s