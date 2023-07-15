from pydantic import BaseModel

import uuid

from utils import BaseResponse

class SmsVerification(BaseModel):
    user_id: uuid.UUID
    code: str

class Credentials(BaseModel):
    username: str
    password: str

class JwtTokens(BaseModel):
    refreshToken: bytes
    accessToken: bytes

class UserSign(BaseModel):
    ip: str
    user_agent: str

class UserId(BaseResponse):
    user_id: uuid.UUID