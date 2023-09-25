import ipaddress
import uuid
from datetime import datetime, timedelta
from operator import and_

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from admin.schemas import ProductsResponse
from admin.utils import get_products_
from auth.routes import get_access_token
from auth.utils import AccessTokenPayload
from database import get_async_session
from payment.models import Purchase, PromoCode
from payment.models import Product as ProductModel
from payment.models import Payment as PaymentModel
from payment.schemas import ProductCode, Amount, Confirmation, ConfirmationUrl, NewPrice
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


@router.post('/url')
async def get_url(product: ProductCode,
                  user_token: AccessTokenPayload=Depends(get_access_token),
                  session: AsyncSession=Depends(get_async_session)) -> ConfirmationUrl:

    product_model = await session.get(ProductModel, product.id)

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
        user_id=user_token.id,
        product_id=product.id
    ))

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
        await session.delete(payment)
        session.add(Purchase(
            id=uuid.uuid4(),
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

@router.post('/promo')
async def check_promo(product: ProductCode,
                      session: AsyncSession=Depends(get_async_session)):

    product_model = await session.get(ProductModel, product.id)

    price = await get_promo_price(
        product_model=product_model,
        product_code=product,
        session=session
    )

    return NewPrice(message='status succes',
                    newPrice=price)
