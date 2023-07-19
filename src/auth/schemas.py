from pydantic import BaseModel

import uuid

from config import DEFAULT_PHONE
from utils import BaseResponse

class SmsVerification(BaseModel):
    phone: str=DEFAULT_PHONE
    code: str='1692'

class Credentials(BaseModel):
    username: str=None
    phone: str=DEFAULT_PHONE
    password: str

class JwtTokens(BaseModel):
    refreshToken: str
    accessToken: str

class RefreshTokenPayload(BaseModel):
    jti: uuid.UUID
    sub: uuid.UUID

class AccessTokenHeader(BaseModel):
    alg: str='HS256'
    typ: str='JWT'

class UserSign(BaseModel):
    ip: str
    user_agent: str

class UserId(BaseResponse):
    user_id: uuid.UUID

class PhoneRequest(BaseModel):
    phone: str=DEFAULT_PHONE

class AccessTokenSchema(BaseModel):
    access_token: str

class Token(BaseResponse):
    token: str

class NewPasswordSchema(BaseModel):
    token: str
    password: str