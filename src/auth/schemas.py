from pydantic import BaseModel

import uuid

from utils import BaseResponse

class SmsVerification(BaseModel):
    phone: str='79115901599'
    code: str='1692'

class Credentials(BaseModel):
    username: str
    password: str

class JwtTokens(BaseModel):
    refreshToken: str
    accessToken: str

class RefreshTokenPayload(BaseModel):
    id: uuid.UUID

class AccessTokenHeader(BaseModel):
    alg: str='HS256'
    typ: str='JWT'

class UserSign(BaseModel):
    ip: str
    user_agent: str

class UserId(BaseResponse):
    user_id: uuid.UUID

class PhoneRequest(BaseModel):
    phone: str='79115901599'