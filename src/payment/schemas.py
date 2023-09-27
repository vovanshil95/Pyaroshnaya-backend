import uuid

from pydantic import BaseModel

from utils import BaseResponse


class ProductCode(BaseModel):
    id: uuid.UUID
    promoCode: str | None

class ProductCodeCategories(ProductCode):
    categories: list[uuid.UUID]

class Amount(BaseModel):
    value: str
    currency: str

class Confirmation(BaseModel):
    type: str
    return_url: str

class Payment(BaseModel):
    amount: Amount
    capture: bool
    confirmation: Confirmation
    description: str

class ConfirmationUrl(BaseResponse):
    url: str


class PromoCode(BaseModel):
    id: uuid.UUID
    code: str
    discountAbsolute: int | None
    discountPercent: int | None

class PromoProduct(BaseModel):
    title: str
    availabilityDurationDays: int | None
    usageCount: int | None
    description: str
    categoryIds: list[uuid.UUID] | None
    expanding: bool

class Product(PromoProduct):
    id: uuid.UUID
    priceRubbles: int
    expandable: bool
    categoriesSize: int | None

class AdminProduct(Product):
    isPromo: bool
    returnUrl: str
    promoCodes: list[PromoCode]

class NewPrice(BaseResponse):
    newPrice: int

class Promo(BaseModel):
    promoCode: str
    categories: list[uuid.UUID] | None

class ProductExpand(BaseModel):
    productToExpand: uuid.UUID
    expandingProduct: uuid.UUID
    promoCode: str | None