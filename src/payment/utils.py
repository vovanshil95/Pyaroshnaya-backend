import uuid
from datetime import datetime

from fastapi import Depends, HTTPException
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from auth.routes import get_access_token
from auth.utils import AccessTokenPayload
from database import get_async_session
from payment.models import ProductCategory, Purchase
from questions.models import Category
from questions.schemas import CategoryId


async def paywall_manager(category_id: CategoryId,
                          session: AsyncSession=Depends(get_async_session),
                          user_token: AccessTokenPayload=Depends(get_access_token)) -> uuid.UUID:
    purchase = (await session.execute(
        select(Purchase)
        .join(ProductCategory)
        .join(Category)
        .where(and_(Purchase.user_id == user_token.id,
                    or_(Purchase.expiration_time.is_(None),
                        Purchase.expiration_time > datetime.now()),
                    or_(Purchase.remaining_uses.is_(None),
                        Purchase.remaining_uses > 0),
                    Category.parent_id == category_id.categoryId))
    )).scalars().first()

    if purchase is None:
        raise HTTPException(status_code=403, detail='Access denied')

    yield category_id.categoryId

    if purchase.remaining_uses is not None:
        purchase.remaining_uses -= 1

async def paywall_manager_test(category_id: CategoryId):
    yield category_id.categoryId