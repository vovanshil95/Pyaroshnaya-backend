from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.schemas import AdminProductsResponse, ProductsResponse
from payment.models import ProductCategory
from payment.models import Product as ProductModel
from payment.models import  PromoCode as PromoCodeModel
from payment.schemas import Product as ProductSchema
from payment.schemas import AdminProduct as AdminProductSchema
from payment.schemas import PromoCode as PromoCodeSchema


async def get_products_(session: AsyncSession, admin: bool=True) -> AdminProductsResponse | ProductsResponse:
    ProductClass = ProductSchema
    ResponseClass = ProductsResponse

    categories = (await session.execute(select(ProductCategory)
                                        .order_by(ProductCategory.category_id))).scalars().all()
    products = (await session.execute(select(ProductModel)
                                      .where(ProductModel.active)
                                      .order_by(ProductModel.price_rubbles))).scalars().all()
    if admin:
        ProductClass = AdminProductSchema
        ResponseClass = AdminProductsResponse
        promos = (await session.execute(select(PromoCodeModel)
                                        .order_by(PromoCodeModel.id))).scalars().all()
        promos_dict = {product.id: [] for product in products}
        for promo in promos:
            if promos_dict.get(promo.product_id) is not None:
                promos_dict[promo.product_id].append(PromoCodeSchema(
                    id=promo.id,
                    code=promo.code,
                    discountAbsolute=promo.discount_absolute,
                    discountPercent=promo.discount_percent
                ))

    categories_dict = {product.id: [] for product in products}
    for category in categories:
        if categories_dict.get(category.product_id) is not None:
            categories_dict[category.product_id].append(category.category_id)

    products = [ProductClass(
        id=product.id,
        title=product.title,
        priceRubbles=product.price_rubbles,
        availabilityDurationDays=product.availability_duration_days,
        usageCount=product.usage_count,
        description=product.description,
        returnUrl=product.return_url if admin else None,
        promoCodes=promos_dict[product.id] if admin else None,
        categoryIds=categories_dict[product.id]
    ) for product in products if product.title != 'free' or admin]

    return ResponseClass(message='status success',
                         data=products)
