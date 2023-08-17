import base64
from datetime import timedelta
from datetime import datetime

from fastapi import Depends, Request, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from auth.models import SmsSend

import hmac
import uuid
from aiohttp import request
import random
import string

from src.config import SHA_KEY, GREEN_SMS_TOKEN, TEST_SMS_CODE
from database import get_async_session


class AccessTokenPayload(BaseModel):
    id: uuid.UUID
    username: str | None
    phone: str
    role: str
    balance: float
    tillDate: int | None
    exp: int


async def check_user_agent(user_agent: str = Header(...)):
    if user_agent is None:
        raise HTTPException(status_code=400, detail='error: User-Agent required')
    return user_agent

class SmsCodeManager:
    def __init__(self, code_type: str='random'):
        assert code_type in ('random', 'constant')
        self.code_type = code_type

    async def __call__(self,
                       client_request: Request,
                       user_agent:str=Depends(check_user_agent),
                       session: AsyncSession=Depends(get_async_session)):
        last_send = (await session.execute(select(SmsSend)
                .where(and_(SmsSend.ip == client_request.client.host,
                            SmsSend.user_agent == user_agent)))).scalars().first()
        if last_send is not None and datetime.utcnow() - last_send.time_send < timedelta(minutes=1):
            raise HTTPException(status_code=429, detail='Too many requests')

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

        if last_send is None:
            last_send = SmsSend(ip=client_request.client.host,
                                user_agent=user_agent,
                                user_id=self.send_to_user_id)
        last_send.time_send = datetime.utcnow()
        session.add(last_send)

    send_to_user_id: uuid.UUID
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