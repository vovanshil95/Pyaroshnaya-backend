import asyncio
import binascii
import random
import string
import uuid
from datetime import datetime, timedelta
import re

from pydantic import ValidationError
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import REFRESH_TTL_DAYS, ACCESS_TTL_MINUTES, DEFAULT_PHONE
from database import get_async_session, async_session_maker
from auth.schemas import Credentials, JwtTokens, UserId, UserSign, SmsVerification, AccessTokenHeader, \
    RefreshTokenPayload, PhoneRequest, Token, NewPasswordSchema, AccessTokenSchema
from auth.models import Auth, RefreshToken
from users.models import User, UnverifiedUser
from users.schemas import NewUser
from auth.utils import encrypt, base64_encode, SmsCodeManager, AccessTokenPayload, base64_decode
from utils import BaseResponse, msc_now

router = APIRouter(prefix='/auth',
                   tags=['auth'])

async def check_user_agent(user_agent: str = Header(...)):
    if not user_agent:
        raise HTTPException(status_code=400, detail='error: User-Agent required')
    return user_agent

async def get_access_token(Authorization: str = Header(...)) -> AccessTokenPayload:
    base64_chars = r'[a-zA-Z0-9=_+-/]'
    pattern = re.compile(rf'^Bearer {base64_chars}+\.{base64_chars}+\.{base64_chars}+$')

    if pattern.match(Authorization) is None:
        raise HTTPException(status_code=401, detail='user is not authorized')
    header, payload, sign = Authorization.split('Bearer ')[1].split('.')

    if not encrypt(header + '.' + payload) == base64_decode(sign):
        raise HTTPException(status_code=498, detail='the access token is invalid')

    user_token = AccessTokenPayload.parse_raw(base64_decode(payload))

    if int(datetime.utcnow().timestamp()) > user_token.exp:
        raise HTTPException(status_code=498, detail='the access token is invalid')

    return user_token

async def get_refresh_token(Authorization: str = Header(...),
                            session: AsyncSession=Depends(get_async_session),
                            user_agent: str=Depends(check_user_agent)) -> RefreshToken:
    try:
        token=RefreshTokenPayload.parse_raw(base64_decode(Authorization.split('Bearer ')[1]))
    except (IndexError, ValueError, binascii.Error, ValidationError):
        raise HTTPException(status_code=498, detail='the refresh token is invalid')

    db_token = (await session.execute(select(RefreshToken)
                        .where(and_(RefreshToken.user_id == token.sub,
                                    RefreshToken.user_agent == user_agent)))).scalars().first()

    if db_token is None:
        raise HTTPException(status_code=404, detail='refresh token not found')
    if db_token.id != token.jti:
        await session.delete(db_token)
        await session.commit()
        raise HTTPException(status_code=401, detail='the refresh token has already been used')

    return db_token


async def check_new_user(request: Request,
                         new_user: NewUser,
                         user_agent: str=Depends(check_user_agent)) -> UserSign:

    async with async_session_maker() as session1,\
            async_session_maker() as session2:
        same_names, same_phones = await asyncio.gather(
            session1.execute(select(User).where(User.name == new_user.username)),
            session2.execute(select(User).where(User.phone == new_user.phone)))

    if same_names.first():
        raise HTTPException(detail='user with same name already exists', status_code=421)
    if same_phones.first():
        raise HTTPException(detail='user with same name already exists', status_code=409)

    return UserSign(ip=request.client.host, user_agent=user_agent)

def generate_access_token(user: User) -> str:
    payload = AccessTokenPayload(id=user.id,
                                 username=user.name,
                                 phone=user.phone,
                                 role=user.role,
                                 balance=user.balance,
                                 tillDate=user.till_date,
                                 exp=int((datetime.utcnow() + timedelta(minutes=ACCESS_TTL_MINUTES)).timestamp()))

    access_token = base64_encode(AccessTokenHeader().json()) + '.' + base64_encode(payload.json())
    signature = base64_encode(encrypt(access_token))
    signed_access_token = access_token + '.' + signature
    return signed_access_token

def get_new_tokens(user: User,
                   user_agent: str,
                   session: AsyncSession) -> JwtTokens:

    refresh_token_id = uuid.uuid4()

    session.add(RefreshToken(id=refresh_token_id,
                             user_id=user.id,
                             user_agent=user_agent,
                             exp=datetime.utcnow() + timedelta(days=REFRESH_TTL_DAYS),
                             valid=True,
                             last_use=datetime.utcnow()))
    refresh_token = base64_encode(RefreshTokenPayload(jti=refresh_token_id, sub=user.id).json())

    tokens = JwtTokens(refreshToken=refresh_token,
                       accessToken=generate_access_token(user))
    return tokens

@router.post('/login', responses={200: {'model': JwtTokens},
                                  401: {'model': BaseResponse, 'description': 'incorrect username and password'},
                                  409: {'model': BaseResponse, 'description': 're-authentication is not allowed'}})
async def login(credentials: Credentials,
                session: AsyncSession=Depends(get_async_session),
                user_agent: str=Depends(check_user_agent)) -> JwtTokens:
    if credentials.username is None and credentials.phone in (DEFAULT_PHONE, None) or \
            credentials.username is not None and credentials.phone not in (DEFAULT_PHONE, None):
        raise HTTPException(status_code=422, detail='either phone number or username must be specified')

    user = (await session.execute(select(User)
                                  .join(Auth)
                                  .where(and_(User.name == credentials.username if credentials.username else
                                                                                User.phone == credentials.phone,
                                              Auth.password == encrypt(credentials.password))))).scalars().first()
    if user is None:
        raise HTTPException(status_code=401, detail='incorrect username and password')

    if (await session.execute(select(RefreshToken.id)\
            .where(and_(RefreshToken.user_id==user.id,
                        RefreshToken.user_agent == user_agent,
                        RefreshToken.valid)))).scalars().all():
        raise HTTPException(status_code=409, detail='re-authentication is not allowed')

    jwt_tokens = get_new_tokens(user, user_agent, session)

    return jwt_tokens

@router.post('/registration', responses={200: {'model': UserId},
                                         400: {'model': BaseResponse, 'description': 'error: User-Agent required'},
                                         421: {'model': BaseResponse, 'description': 'user with same name already exists'},
                                         409: {'model': BaseResponse, 'description': 'user with same phone already exists'},
                                         429: {'model': BaseResponse, 'description': 'too many requests'}})
async def register(new_user: NewUser,
                   session: AsyncSession=Depends(get_async_session),
                   user_sign: UserSign=Depends(check_new_user),
                   sender: SmsCodeManager=Depends(SmsCodeManager(code_type='constant'))) -> BaseResponse:
    if new_user.phone in (DEFAULT_PHONE, None):
        raise HTTPException(status_code=422, detail='phone number must be specified')
    new_user_id = uuid.uuid4()
    sender.phone=new_user.phone
    session.add(UnverifiedUser(id=new_user_id,
                               ip=user_sign.ip,
                               last_sms_code=sender.code,
                               last_sms_time=msc_now(),
                               user_agent=user_sign.user_agent,
                               username=new_user.username,
                               phone=new_user.phone,
                               company=new_user.company,
                               password=encrypt(new_user.password)))

    return BaseResponse(message='registration status success, SMS-code was sent')

@router.post('/smsCode', responses={200: {'model': JwtTokens},
                                    400: {'model': BaseResponse, 'description': 'error: User-Agent required'},
                                    421: {'model': BaseResponse, 'description': 'code is failed'},
                                    404: {'model': BaseResponse, 'description': 'user not found'}})
async def code_verification(verification: SmsVerification,
                            user_agent: str=Depends(check_user_agent),
                            session: AsyncSession=Depends(get_async_session)) -> JwtTokens:

    new_user = (await session.execute(select(UnverifiedUser)
                        .filter(and_(UnverifiedUser.user_agent==user_agent,
                                     UnverifiedUser.phone==verification.phone)))).scalars().first()
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
    await session.flush()
    tokens = get_new_tokens(user=user, user_agent=user_agent, session=session)
    await session.delete(new_user)

    session.add(Auth(id=uuid.uuid4(),
                     user_id=user.id,
                     password=new_user.password))

    return tokens


@router.post('/logout', responses={200: {'model': BaseResponse},
                                   300: {'model': BaseResponse, 'description': 'user is blocked'},
                                   400: {'model': BaseResponse, 'description': 'error: User-Agent required'},
                                   401: {'model': BaseResponse, 'description': 'user is not authorized'},
                                   498: {'model': BaseResponse, 'description': 'the access token is invalid'}})
async def logout(user_token: AccessTokenPayload=Depends(get_access_token),
                 user_agent: str=Depends(check_user_agent),
                 session: AsyncSession=Depends(get_async_session)) -> BaseResponse:

    refresh_tokens = (await session.execute(select(RefreshToken)
                           .where(and_(RefreshToken.user_agent == user_agent,
                                       RefreshToken.user_id == user_token.id)))).all()

    if refresh_tokens == []:
        await session.execute(delete(RefreshToken).filter(RefreshToken.id == user_token.id))
        raise HTTPException(status_code=300, detail='user is blocked')

    await session.execute(delete(RefreshToken)
                          .where(and_(RefreshToken.user_agent == user_agent,
                                      RefreshToken.user_id == user_token.id)))

    return BaseResponse(message='status success, user logged out')

@router.post('/passwordRecovery', responses={200: {'model': BaseResponse},
                                             421: {'model': BaseResponse, 'description': 'The phone number was not found'},
                                             429: {'model': BaseResponse, 'description': 'Too many requests'}})
async def get_phone(phone_request: PhoneRequest,
                    session: AsyncSession=Depends(get_async_session),
                    sms_sender: SmsCodeManager=Depends(SmsCodeManager(code_type='constant'))):
    if (user := (await session.execute(select(User).filter(User.phone == phone_request.phone))).scalars().first()) is None:
        raise HTTPException(status_code=421, detail='The phone number was not found')

    sms_sender.phone = phone_request.phone
    auth = (await session.execute(select(Auth).filter(Auth.user_id == user.id))).scalars().first()
    auth.sms_code = sms_sender.code

    return BaseResponse(message='status success: SMS-code was sent')

@router.put('/passwordRecovery', responses={200: {'model': BaseResponse},
                                            404: {'model': BaseResponse, 'description': 'user not found'},
                                            421: {'model': BaseResponse, 'description': 'code is failed'}})
async def code_verification_recovery(verification: SmsVerification,
                                     session: AsyncSession=Depends(get_async_session)):
    auth = (await session.execute(select(Auth).join(User).where(User.phone == verification.phone))).scalars().first()
    if auth is None:
        raise HTTPException(status_code=404, detail='user not found')
    if auth.sms_code is None or auth.sms_code != verification.code:
        raise HTTPException(status_code=421, detail='code is failed')

    token = ''.join(random.choices(string.ascii_lowercase + string.digits, k=64))

    auth.sms_code = None
    auth.token = token
    auth.token_exp_time = datetime.utcnow() + timedelta(minutes=ACCESS_TTL_MINUTES)
    session.add(auth)

    return Token(message='status success, phone verified', token=token)

@router.post('/newPassword', responses={200: {'model': BaseResponse},
                                        498: {'model': BaseResponse, 'description': 'the access token is invalid'}})
async def get_new_password(new_pass: NewPasswordSchema,
                           session: AsyncSession=Depends(get_async_session)):
    auth = (await session.execute(select(Auth).filter(Auth.token==new_pass.token))).scalars().first()
    if auth is None:
        raise HTTPException(status_code=498, detail='the access token is invalid')

    auth.token = None

    if datetime.utcnow() > auth.token_exp_time:
        auth.token_exp_time = None
        session.add(auth)
        await session.commit()
        raise HTTPException(status_code=498, detail='the access token is invalid')

    auth.token_exp_time = None
    auth.password = encrypt(new_pass.password)
    session.add(auth)

    return BaseResponse(message='status success, phone verified')

@router.get('/newTokens', responses={200: {'model': JwtTokens},
                                     400: {'model': BaseResponse, 'description': 'attempt to update non-expired token, token revoked'},
                                     401: {'model': BaseResponse, 'description': 'the refresh token has already been used'},
                                     404: {'model': BaseResponse, 'description': 'refresh token not found'},
                                     498: {'model': BaseResponse, 'description': 'the refresh token is invalid'}})
async def give_new_tokens(refresh_token: RefreshToken=Depends(get_refresh_token),
                        session: AsyncSession=Depends(get_async_session)) -> JwtTokens:

    if refresh_token.exp > datetime.utcnow():
        raise HTTPException(status_code=400, detail='attempt to update non-expired token, token revoked')

    user = await session.get(User, refresh_token.user_id)
    await session.delete(refresh_token)

    new_tokens = get_new_tokens(user=user,
                                user_agent=refresh_token.user_agent,
                                session=session)

    return new_tokens

@router.get('/newAccessToken', responses={200: {'model': JwtTokens},
                                          400: {'model': BaseResponse, 'description': 'attempt to update non-expired token, refresh token revoked'},
                                          401: {'model': BaseResponse, 'description': 'the refresh token has already been used'},
                                          403: {'model': BaseResponse, 'description': 'refresh token expired'},
                                          404: {'model': BaseResponse, 'description': 'refresh token not found'},
                                          498: {'model': BaseResponse, 'description': 'the refresh token is invalid'}})
async def get_access_token(refresh_token: RefreshToken=Depends(get_refresh_token),
                           session: AsyncSession=Depends(get_async_session)) -> AccessTokenSchema:
    if datetime.utcnow() > refresh_token.exp:
        raise HTTPException(status_code=403, detail='refresh token expired')

    if datetime.utcnow() < refresh_token.last_use + timedelta(minutes=ACCESS_TTL_MINUTES):
        await session.delete(refresh_token)
        await session.commit()
        raise HTTPException(status_code=400, detail='attempt to update non-expired token, refresh token revoked')

    user = await session.get(User, refresh_token.user_id)

    refresh_token.last_use = datetime.utcnow()
    session.add(refresh_token)

    return AccessTokenSchema(access_token=generate_access_token(user))
