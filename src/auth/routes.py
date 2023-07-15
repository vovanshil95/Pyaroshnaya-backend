import asyncio
import random
import uuid
from datetime import datetime, timedelta
import string
import re

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config import REFRESH_TTL_DAYS, ACCESS_TTL_MINUTES
from database import get_async_session, async_session_maker
from auth.schemas import Credentials, JwtTokens, UserId, UserSign, SmsVerification
from auth.models import Auth, RefreshToken, TokenGroup
from users.models import User, UnverifiedUser
from users.schemas import NewUser
from auth.utils import encrypt, base64_encode, SmsSender, AccessTokenPayload, access_token_header, base64_decode
from utils import BaseResponse, msc_now

router = APIRouter(prefix='/auth',
                   tags=['auth'])

async def check_user_agent(user_agent: str = Header(...)):
    if not user_agent:
        raise HTTPException(status_code=400, detail='error: User-Agent required')
    return user_agent

async def get_user_token(request: Request) -> AccessTokenPayload:
    if (auth_header := request.headers.get('Authorization')) is None:
        raise HTTPException(status_code=401, detail='User is not authorized')

    base64_chars = r'[a-zA-Z0-9+/]'
    pattern = re.compile(rf'^Barier {base64_chars}+\.{base64_chars}+\.{base64_chars}+$')

    if pattern.match(auth_header) in None:
        raise HTTPException(status_code=401, detail='User is not authorized')
    header, payload, sign = auth_header.split('.')

    if not encrypt(header + '.' + payload) == base64_decode(sign):
        raise HTTPException(status_code=498, detail='The access token is invalid')

    user_token = AccessTokenPayload.parse_raw(base64_decode(payload))

    if int(datetime.utcnow()) > user_token.exp:
        raise HTTPException(status_code=498, detail='The access token is invalid')

    return user_token


async def check_new_user(request: Request,
                         new_user: NewUser,
                         user_agent: str=Depends(check_user_agent)) -> UserSign:

    async with async_session_maker() as session1,\
            async_session_maker() as session2,\
            async_session_maker() as session3:
        same_names, same_phones, recent_requests = await asyncio.gather(
            session1.execute(select(User).where(User.name == new_user.username)),
            session2.execute(select(User).where(User.phone == new_user.phone)),
            session3.execute(select(UnverifiedUser).where(
                    and_(UnverifiedUser.user_agent == user_agent,
                         UnverifiedUser.ip == request.client.host,
                         (msc_now() - UnverifiedUser.last_sms_time) < timedelta(minutes=1))))
        )

    if same_names.first():
        raise HTTPException(detail='user with same name already exists', status_code=421)
    if same_phones.first():
        raise HTTPException(detail='user with same name already exists', status_code=422)
    if recent_requests.first():
        raise HTTPException(detail='too many requests', status_code=429)

    return UserSign(ip=request.client.host, user_agent=user_agent)

async def get_new_tokens(user: User,
                         user_agent: str,
                         session: AsyncSession) -> JwtTokens:
    group_id = uuid.uuid4()
    session.add(TokenGroup(id=group_id))
    await session.flush()

    session.add(RefreshToken(user_id=user.id,
                             user_agent=user_agent,
                             exp=datetime.utcnow() + timedelta(days=REFRESH_TTL_DAYS),
                             valid=True,
                             token_group_id=group_id,
                             last_use=msc_now()))
    payload = AccessTokenPayload(id=user.id,
                                 username=user.name,
                                 phone=user.phone,
                                 role=user.role,
                                 balance=user.balance,
                                 tillDate=user.till_date,
                                 exp=int(datetime.utcnow() + timedelta(minutes=ACCESS_TTL_MINUTES)))

    access_token = base64_encode(access_token_header) + b'.' + base64_encode(payload)
    signature = base64_encode(encrypt(access_token))
    signed_access_token = access_token + b'.' + signature
    refresh_token = base64_encode({id: user.id})

    tokens = JwtTokens(refreshToken=refresh_token,
                       accessToken=signed_access_token)
    return tokens

@router.post('/login')
async def login(credentials: Credentials,
                session: AsyncSession=Depends(get_async_session),
                user_agent: str=Depends(check_user_agent)) -> JwtTokens:
    user = (await session.execute(select(User)
                                  .join(Auth)
                                  .where(and_(User.name == credentials.username,
                                              Auth.password == encrypt(credentials.password))))).first()
    if not user.id:
        raise HTTPException(status_code=400, detail='incorrect username and password')

    if corrupted_token_group := await select(RefreshToken)\
            .where(and_(RefreshToken.user_id==user.id,
                        RefreshToken.user_agent == user_agent,
                        RefreshToken.valid)).token_group_id:
        corrupted_tokens = await session.execute(select(RefreshToken)
                                 .where(RefreshToken.token_group_id == corrupted_token_group)).scalars().all()
        for token in corrupted_tokens:
            token.valid = False
        await session.bulk_update_mappings(RefreshToken, corrupted_tokens)
        await session.commit()
        raise HTTPException(status_code=409, detail='re-authentication is not allowed')

    jwt_tokens = await get_new_tokens(user, user_agent)

    return jwt_tokens

@router.post('/registration', responses={200: {'model': UserId},
                                         400: {'model': BaseResponse, 'description': 'error: User-Agent required'},
                                         421: {'model': BaseResponse, 'description': 'user with same name already exists'},
                                         422: {'model': BaseResponse, 'description': 'user with same phone already exists'},
                                         429: {'model': BaseResponse, 'description': 'too many requests'}})
async def register(new_user: NewUser,
                   session: AsyncSession=Depends(get_async_session),
                   user_sign: UserSign=Depends(check_new_user),
                   sender: SmsSender =Depends(SmsSender())) -> UserId:

    sms_code = "".join(random.choices(string.digits, k=4))
    sender.phone = new_user.phone
    sender.code = sms_code

    new_user_id = uuid.uuid4()
    session.add(UnverifiedUser(id=new_user_id,
                               ip=user_sign.ip,
                               last_sms_code=sms_code,
                               last_sms_time=msc_now(),
                               user_agent=user_sign.user_agent,
                               username=new_user.username,
                               phone=new_user.phone,
                               company=new_user.company,
                               password=encrypt(new_user.password)))

    return UserId(message='registration status success, SMS-code was sent', user_id=new_user_id)

@router.post('auth/smsCode', responses={200: {'model': JwtTokens},
                                        400: {'model': BaseResponse, 'description': 'error: User-Agent required'},
                                        421: {'model': BaseResponse, 'description': 'code is failed'},
                                        404: {'model': BaseResponse, 'description': 'user not found'}})
async def code_verification(verification: SmsVerification,
                            user_agent: str=Depends(check_user_agent),
                            session: AsyncSession=Depends(get_async_session)) -> JwtTokens:

    new_user = await session.get(UnverifiedUser, verification.user_id)
    if not new_user:
        raise HTTPException(status_code=404, detail='user not found')
    if new_user.last_sms_code != verification.code:
        raise HTTPException(status_code=421, detail='code is failed')

    user = User(id=new_user.id,
                name=new_user.username,
                phone=new_user.phone,
                company=new_user.company,
                role='user',
                balance=0,
                till_date=None)

    session.add(user)

    tokens = await get_new_tokens(user=user, user_agent=user_agent, session=session)
    await session.flush()
    await session.delete(new_user)

    session.add(Auth(id=uuid.uuid4(),
                     user_id=user.id,
                     password=new_user.password))

    return tokens


@router.post('/logout')
def logout(user_token: User=Depends(get_user_token),
           session: AsyncSession=Depends(get_async_session)):
    pass