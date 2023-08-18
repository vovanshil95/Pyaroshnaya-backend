import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import RefreshToken
from users.models import User
from users.schemas import UserProfileResponse, UserProfile


async def get_profile(session: AsyncSession, user_id: uuid.UUID, user_agent: str) -> UserProfileResponse:
    user = await session.get(User, user_id)

    theme = (await session.execute(
        select(RefreshToken.theme)
        .where(and_(RefreshToken.user_id == user_id,
                    RefreshToken.user_agent == user_agent)))).scalar()

    theme = 'LIGHT_THEME' if theme is None else theme

    return UserProfileResponse(
        message='status success',
        data=UserProfile(
            id=user.id,
            username=user.name,
            company=user.company,
            theme=theme
        )
    )