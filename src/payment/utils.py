import uuid
from datetime import datetime

from fastapi import Depends, HTTPException
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from auth.routes import get_access_token
from auth.utils import AccessTokenPayload
from database import get_async_session
from payment.models import ProductCategory, Purchase, PurchaseCategory
from questions.models import Category
from questions.schemas import CategoryId


class Paywall:
    symbols_in_response: int
    category_id: uuid.UUID

class PaywallManager(Paywall):
    async def __call__(self,
                       category_id: CategoryId,
                       session: AsyncSession=Depends(get_async_session),
                       user_token: AccessTokenPayload=Depends(get_access_token)) -> uuid.UUID:

        self.category_id = category_id.categoryId

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
            purchase = (await session.execute(
                select(Purchase)
                .join(PurchaseCategory)
                .join(Category)
                .where(and_(
                    Purchase.user_id == user_token.id,
                    or_(Purchase.expiration_time.is_(None),
                        Purchase.expiration_time > datetime.now()),
                    or_(Purchase.remaining_uses.is_(None),
                        Purchase.remaining_uses > 0),
                    Category.parent_id == category_id.categoryId
                    ))
            )).scalars().first()

        if purchase is None:
            raise HTTPException(status_code=403, detail='Access denied')

        yield self

        if purchase.remaining_uses is not None:
            purchase.remaining_uses = max(0, purchase.remaining_uses - self.symbols_in_response)

class PaywallManagerTest(Paywall):
    def __call__(self, category_id: CategoryId):
        self.category_id = category_id.categoryId
        yield self