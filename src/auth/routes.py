import asyncio
import base64
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config import JWT_TTL_DAYS
from database import get_async_session
from auth.schemas import Credentials, JwtTokens
from auth.models import Auth, RefreshToken, TokenGroup
from users.models import User, UnverifiedUser
from users.schemas import NewUser
from auth.utils import encrypt

router = APIRouter(prefix='/auth',
                   tags=['auth'])

async def check_user_agent(user_agent: str = Header(...)):
    if not user_agent:
        raise HTTPException(status_code=400, detail='error: User-Agent required')
    return user_agent

def get_access_token():
    return None

@router.post('/login')
async def login(credentials: Credentials,
                session: AsyncSession=Depends(get_async_session),
                user_agent: str=Depends(check_user_agent)) -> JwtTokens:
    user_id = (await session.execute(select(User.id)
                                  .join(Auth)
                                  .where(and_(User.name == credentials.username,
                                              Auth.password == encrypt(credentials.password))))).first()
    if not user_id:
        raise HTTPException(status_code=400, detail='incorrect username and password')

    if corrupted_token_group := await select(RefreshToken)\
            .where(and_(RefreshToken.user_id==user_id,
                        RefreshToken.user_agent == user_agent,
                        RefreshToken.valid)).token_group_id:
        corrupted_tokens = await session.execute(select(RefreshToken)
                                 .where(RefreshToken.token_group_id == corrupted_token_group)).scalars().all()
        for token in corrupted_tokens:
            token.valid = False
        await session.bulk_update_mappings(RefreshToken, corrupted_tokens)
        session.commit() # посмотреть работпет ли без него
        raise HTTPException(status_code=409, detail='re-authentication is not allowed')



    group_id = uuid.uuid4()
    session.add(TokenGroup(group_id))
    await session.flush()

    session.add(RefreshToken(user_id=user_id,
                             user_agent=user_agent,
                             till_date=datetime.now() + timedelta(days=JWT_TTL_DAYS),
                             valid=True,
                             token_group_id=group_id))

    access_token = get_access_token()

    return JwtTokens(refreshToken=base64.urlsafe_b64encode(str({id: user_id})),
                     accessToken=access_token)

@router.post('/registration')
async def register(new_user: NewUser,
                   request: Request,
                   session: AsyncSession=Depends(get_async_session),
                   user_agent: str=Depends(check_user_agent)):
    same_names, same_phones, recent_requests = await asyncio.gather(
        session.execute(select(User).where(User.name == new_user.name)),
        session.execute(select(User).where(User.phone == new_user.phone)),
        session.execute(session.execute(select(UnverifiedUser)
                .where(and_(UnverifiedUser.user_agent == user_agent,
                            UnverifiedUser.ip == request.client.host,
                            (datetime.now() - UnverifiedUser.last_sms_time) < timedelta(minutes=1)))))
    )
    if same_names.first():
        raise HTTPException(status_code=421, detail='user with same name already exists')
    if same_phones.first():
        raise HTTPException(status_code=422, detail='user with same phone already exists')
    if recent_requests.first():
        raise HTTPException(status_code=429, detail='Too many requests')

    return None