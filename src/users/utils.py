import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import RefreshToken
from payment.models import Product, ProductCategory, Purchase, PurchaseCategory
from payment.schemas import UserAccess
from users.models import User
from users.schemas import UserProfileResponse, UserProfile

async def get_access(session: AsyncSession, user_id: uuid.UUID) -> UserAccess:
    
    category_ids = set((await session.execute(
        select(PurchaseCategory.category_id)
        .join(Purchase)
        .where(Purchase.user_id == user_id)
        )).scalars().all())

    category_ids = category_ids.union(set((await session.execute(
        select(ProductCategory.category_id)
        .join(Product)
        .join(Purchase)
        .where(Purchase.user_id == user_id)
        )).scalars().all()))
    
    purchase = (await session.execute(
        select(Purchase)
        .join(Product)
        .where(and_(Purchase.user_id == user_id,
                    Product.title != 'free'))
        )).scalars().first()
    
    return UserAccess(remainingUses=purchase.remaining_uses if purchase else None,
                      categoryIds=list(category_ids),
                      expirationTime=purchase.expiration_time if purchase else None)
    



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
            theme=theme,
            access=await get_access(
                session=session,
                user_id=user_id
            )
        )
    )
