from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import RefreshToken
from auth.routes import get_access_token
from auth.utils import AccessTokenPayload, check_user_agent
from database import get_async_session
from users.models import User
from users.schemas import UserProfile, UserProfileResponse, Theme, Username
from src.utils import BaseResponse
from users.utils import get_profile

router = APIRouter(prefix='/profile',
                   tags=['Profile'])

@router.get('/profile', responses={200: {'model': UserProfile},
                                        400: {'model': BaseResponse, 'description': 'error: User-Agent required'},
                                        401: {'model': BaseResponse, 'description': 'user is not authorized'},
                                        498: {'model': BaseResponse, 'description': 'the access token is invalid'}})
async def get_profile_route(user_agent: str=Depends(check_user_agent),
                            session: AsyncSession=Depends(get_async_session),
                            access_token: AccessTokenPayload=Depends(get_access_token)) -> UserProfileResponse:
    return await get_profile(session, access_token.id, user_agent)

@router.post('/changeUsername', responses={200: {'model': UserProfile},
                                                400: {'model': BaseResponse, 'description': 'error: User-Agent required'},
                                                401: {'model': BaseResponse, 'description': 'user is not authorized'},
                                                409: {'model': BaseResponse, 'description': 'Username is already taken'},
                                                498: {'model': BaseResponse, 'description': 'the access token is invalid'}})
async def get_profile_route(username: Username,
                            user_agent: str=Depends(check_user_agent),
                            session: AsyncSession=Depends(get_async_session),
                            access_token: AccessTokenPayload=Depends(get_access_token)) -> UserProfileResponse:

    if (await session.execute(select(User).where(User.name == username.username))).scalar() is not None:
        raise HTTPException(status_code=409, detail='Username is already taken')

    await session.execute(update(User).where(User.id == access_token.id).values(name=username.username))
    await session.flush()
    return await get_profile(session, access_token.id, user_agent)

@router.post('/changeTheme', responses={200: {'model': UserProfile},
                                             400: {'model': BaseResponse, 'description': 'error: User-Agent required'},
                                             401: {'model': BaseResponse, 'description': 'user is not authorized'},
                                             498: {'model': BaseResponse, 'description': 'the access token is invalid'}})
async def changeTheme(theme: Theme,
                      user_agent: str=Depends(check_user_agent),
                      session: AsyncSession=Depends(get_async_session),
                      access_token: AccessTokenPayload=Depends(get_access_token)):
    await session.execute(update(RefreshToken).where(and_(RefreshToken.user_id == access_token.id,
                        RefreshToken.user_agent == user_agent)).values(theme=theme.theme))
    await session.flush()

    return await get_profile(session, access_token.id, user_agent)