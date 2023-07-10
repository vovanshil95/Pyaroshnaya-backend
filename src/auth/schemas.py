from pydantic import BaseModel

import uuid


class AccessTokenPayload(BaseModel):
    id: uuid.UUID
    username: str
    phone: str
    role: str
    balance: float
    tillDate: int

class SmsVerification(BaseModel):
    user_id: uuid.UUID
    code: int
