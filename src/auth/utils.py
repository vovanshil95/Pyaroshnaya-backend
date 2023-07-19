import base64
from datetime import timedelta
from datetime import datetime

from fastapi import Depends, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from auth.models import SmsSend
from utils import msc_now

import hmac
import uuid
from aiohttp import request
import random
import string

from config import SHA_KEY, GREEN_SMS_TOKEN, TEST_SMS_CODE
from database import get_async_session


class AccessTokenPayload(BaseModel):
    id: uuid.UUID
    username: str | None
    phone: str
    role: str
    balance: float
    tillDate: int | None
    exp: int

class SmsCodeManager:
    def __init__(self, code_type: str='random'):
        assert code_type in ('random', 'constant')
        self.code_type = code_type

    async def __call__(self,
                       client_request: Request,
                       session: AsyncSession=Depends(get_async_session)):
        last_send = await session.get(SmsSend, client_request.client.host)
        if last_send is None:
            last_send = SmsSend(ip=client_request.client.host)
        elif datetime.now() - last_send.time_send < timedelta(minutes=1 if self.code_type == 'random' else 0):
            raise HTTPException(status_code=429, detail='Too many requests')

        last_send.time_send = msc_now()
        session.add(last_send)

        if self.code_type == 'random':
            self.code = "".join(random.choices(string.digits, k=4))
        elif self.code_type == 'constant':
            self.code = TEST_SMS_CODE
        yield self
        if self.code_type == 'random':
            async with request(method='POST',
                               url='https://api3.greensms.ru/sms/send',
                               headers={'Authorization': f'Bearer {GREEN_SMS_TOKEN}'},
                               data={'to': self.phone, 'txt': f'code {self.code}', 'from': 'Пярошная'}) as resp:
                await resp.json()

    code: str
    phone: str
    code_type: str

def encrypt(string: str | bytes) -> bytes:
    return hmac.new(SHA_KEY, string.encode() if isinstance(string, str) else string, 'sha256').digest()

def base64_encode(content: str | bytes) -> str:
    if isinstance(content, str):
        content = content.encode()
    return base64.urlsafe_b64encode(content).decode()

def base64_decode(content: str) -> bytes:
    return base64.urlsafe_b64decode(content)