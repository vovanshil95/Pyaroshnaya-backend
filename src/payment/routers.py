import ipaddress
import uuid
from datetime import datetime, timedelta
from operator import and_
from typing import Tuple

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from admin.schemas import ProductsResponse
from admin.utils import get_products_
from auth.routes import get_access_token
from auth.utils import AccessTokenPayload
from database import get_async_session
from payment.models import Purchase, PromoCode, PaymentCategory, PurchaseCategory, ProductCategory
from payment.models import Product as ProductModel
from payment.models import Payment as PaymentModel
from payment.schemas import ProductCode, Amount, Confirmation, ConfirmationUrl, NewPrice, ProductCodeCategories, Promo, \
    ProductExpand
from payment.schemas import PromoProduct
from payment.schemas import Payment as PaymentSchema
from config import SHOP_ID, SHOP_KEY, YOOKASSA_NETWORKS
from utils import BaseResponse

router = APIRouter(prefix='/pay',
                   tags=['Payment'])

async def get_promo_price(product_model: ProductModel,
                          session: AsyncSession,
                          product_code) -> int:
    price = product_model.price_rubbles

    if product_code.promoCode is not None:
        promo_code = (await session.execute(
            select(PromoCode)
            .where(and_(
                PromoCode.product_id == product_code.id,
                PromoCode.code == product_code.promoCode
            )))
        ).scalars().first()
        if promo_code is None:
            raise HTTPException(status_code=404, detail='promo_code not found')
        else:
            price = max(price - promo_code.discount_absolute, 0) \
                if promo_code.discount_absolute is not None else price
            price = int(price * (1 - promo_code.discount_percent / 100)) \
                if promo_code.discount_percent is not None else price

    return price

async def get_payment_url(product_model: ProductModel,
                          product: ProductCodeCategories,
                          user_id: uuid.UUID,
                          session: AsyncSession,
                          product_to_expend_id: uuid.UUID=None) -> Tuple[uuid.UUID, str]:
    price = await get_promo_price(
        product_model=product_model,
        product_code=product,
        session=session
    )

    payment = PaymentSchema(
        amount=Amount(
            value=str(price),
            currency='RUB'
        ),
        capture=True,
        confirmation=Confirmation(
            type='redirect',
            return_url=product_model.return_url
        ),
        description=product_model.description
    ).json()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://api.yookassa.ru/v3/payments',
            auth=(SHOP_ID, SHOP_KEY),
            headers={'Content-Type': 'application/json',
                     'Idempotence-Key': uuid.uuid4().hex},
            data=payment
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail='Payment service is unavailable')

    url = response.json()['confirmation']['confirmation_url']
    payment_id = uuid.UUID(hex=response.json()['id'])

    session.add(PaymentModel(
        id=payment_id,
        user_id=user_id,
        product_id=product_model.id,
        product_to_expend_id=product_to_expend_id
    ))

    return payment_id, url


@router.post('/url')
async def get_url(product: ProductCodeCategories,
                  user_token: AccessTokenPayload=Depends(get_access_token),
                  session: AsyncSession=Depends(get_async_session)) -> ConfirmationUrl:

    product_model = await session.get(ProductModel, product.id)

    payment_id, url = await get_payment_url(
        product_model=product_model,
        product=product,
        user_id=user_token.id,
        session=session
    )

    if product_model.categories_size is not None:
        if len(product.categories) != product_model.categories_size:
            raise HTTPException(status_code=403, detail='invalid number of categories')
        await session.flush()
        session.add_all([PaymentCategory(payment_id=payment_id,
                                         category_id=category_id)
                         for category_id in product.categories])

    return ConfirmationUrl(message='status success',
                           url=url)

@router.post('/expand')
async def expand(products: ProductExpand,
                 session: AsyncSession=Depends(get_async_session),
                 user_token: AccessTokenPayload=Depends(get_access_token)) -> ConfirmationUrl:

    product_model = await session.get(ProductModel, products.expandingProduct)
    product_to_expand = await session.get(ProductModel, products.productToExpand)
    if not product_to_expand.expandable:
        raise HTTPException(status_code=403, detail='product is not expandable')
    if not product_model.expanding:
        raise HTTPException(status_code=403, detail='product is not expanding')

    _, url = await get_payment_url(
        product_model=product_model,
        product=ProductCodeCategories(id=product_model.id, code=products.promoCode, categories=[]),
        user_id=user_token.id,
        session=session,
        product_to_expend_id=products.productToExpand
    )

    return ConfirmationUrl(message='status success',
                           url=url)

@router.post('/succeeded')
async def confirm(request: Request,
                  confirmation: dict,
                  session: AsyncSession=Depends(get_async_session)) -> BaseResponse:
    ip = ipaddress.ip_address(request.client.host)
    if not any([ip in network for network in YOOKASSA_NETWORKS]):
        raise HTTPException(status_code=403, detail='this endpoint is only for yookassa')
    if confirmation['event'] == 'payment.succeeded':
        payment_id = uuid.UUID(hex=confirmation['object']['id'])
        payment = await session.get(PaymentModel, payment_id)
        product = await session.get(ProductModel, payment.product_id)

        if product.expanding:
            purchase = (await session.execute(
                select(Purchase)
                .where(Purchase.product_id == payment.product_to_expend_id)
            )).scalars().first()
            purchase.remaining_uses += product.usage_count
            await session.delete(payment)
            return BaseResponse(message='status success')

        categories = (await session.execute(
            select(PaymentCategory.category_id).where(PaymentCategory.payment_id == payment_id)
        )).scalars().all()

        purchase_id = uuid.uuid4()

        session.add_all([PurchaseCategory(purchase_id=purchase_id,
                                          category_id=category_id)
                         for category_id in categories])
        await session.delete(payment)
        free_product = (await session.execute(select(ProductModel).where(ProductModel.title == 'free'))).scalars().first()
        await session.execute(
            delete(Purchase)
            .where(and_(Purchase.user_id == payment.user_id,
                        Purchase.product_id != free_product.id))
            )
        session.add(Purchase(
            id=purchase_id,
            user_id=payment.user_id,
            product_id=payment.product_id,
            expiration_time=datetime.now() + timedelta(days=product.availability_duration_days)
            if product.availability_duration_days is not None else None,
            remaining_uses=product.usage_count
        ))

    return BaseResponse(message='status success')

@router.get('/products', dependencies=[Depends(get_access_token)])
async def get_products(session: AsyncSession=Depends(get_async_session)) -> ProductsResponse:
    return await get_products_(session=session,
                               admin=False)

@router.get('/promo', dependencies=[Depends(get_access_token)])
async def check_promo(productId: uuid.UUID,
                      promoCode: str,
                      session: AsyncSession=Depends(get_async_session)) -> NewPrice:
    if productId is not None:
        product_model = await session.get(ProductModel, productId)

        price = await get_promo_price(
            product_model=product_model,
            product_code=ProductCode(id=productId, promoCode=promoCode),
            session=session
        )

    return NewPrice(message='status succes',
                    newPrice=price)

@router.post('/promo')
async def apply_promo(promo: Promo,
                      user_token: AccessTokenPayload=Depends(get_access_token),
                      session: AsyncSession=Depends(get_async_session)) -> PromoProduct:
    product = (await session.execute(
        select(ProductModel)
        .join(PromoCode)
        .where(and_(PromoCode.code == promo.promoCode,
                    ProductModel.is_promo))
    )).scalars().first()

    if product is None:
        raise HTTPException(status_code=404, detail='promo_code not found')

    purchase_id = uuid.uuid4()

    if product.categories_size is not None:
        categories = promo.categories
        if product.categories_size != len(Promo.categories):
            raise HTTPException(status_code=403, detail='invalid number of categories')
        session.add_all([PurchaseCategory(purchase_id=purchase_id,
                                          category_id=category_id)
                         for category_id in promo.categories])
    else:
        categories = (await session.execute(
            select(ProductCategory)
            .where(ProductCategory.product_id == product.id))
                      ).scalars().all()

    session.add(Purchase(
        id=purchase_id,
        user_id=user_token.id,
        product_id=product.id,
        expiration_time=datetime.now() + timedelta(days=product.availability_duration_days)
        if product.availability_duration_days is not None else None,
        remaining_uses=product.usage_count
    ))

    return PromoProduct(title=product.title,
                        availabilityDurationDays=product.availability_duration_days,
                        usageCount=product.usage_count,
                        description=product.description,
                        categoryIds=categories)