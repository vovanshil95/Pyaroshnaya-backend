from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from users.models import User
from users.schemas import User as UserSchema
from database import get_async_session

router = APIRouter(prefix='/api/users',
                   tags=['Users'])

@router.get('')
async def get_users(session: AsyncSession = Depends(get_async_session)) -> list[UserSchema]:
    users = await session.execute(select(User))
    return list(map(lambda user: UserSchema(id=user[0].id, name=user[0].name), users))
