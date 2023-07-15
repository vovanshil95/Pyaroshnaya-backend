from _datetime import datetime, timedelta

from pydantic import BaseModel

def msc_now() -> datetime:
    return datetime.utcnow() + timedelta(hours=3)

class BaseResponse(BaseModel):
    message: str