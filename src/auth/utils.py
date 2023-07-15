import base64

from pydantic import BaseModel

import hmac
import uuid
from aiohttp import request

from config import SHA_KEY, GREEN_SMS_TOKEN

class AccessTokenPayload(BaseModel):
    id: uuid.UUID
    username: str
    phone: str
    role: str
    balance: float
    tillDate: int | None
    exp: int

class SmsSender:
    async def __call__(self):
        yield self
        async with request(method='POST',
                           url='https://api3.greensms.ru/sms/send',
                           headers={'Authorization': f'Bearer {GREEN_SMS_TOKEN}'},
                           data={'to': self.phone, 'txt': f'code {self.code}', 'from': 'hello'}) as resp:
            await resp.json()

def encrypt(string: str | bytes) -> bytes:
    return hmac.new(SHA_KEY, string.encode() if isinstance(string, str) else string, 'sha256').digest()

def base64_encode(content: str | dict) -> bytes:
    return base64.urlsafe_b64encode((content if isinstance(content, str) else str(content)).encode())

def base64_decode(content: bytes | str) -> bytes:
    return base64.urlsafe_b64decode(content)

access_token_header = {'alg': 'HS256', 'typ': 'JWT'}
