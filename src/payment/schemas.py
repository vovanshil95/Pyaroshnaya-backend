import uuid

from pydantic import BaseModel

from utils import BaseResponse


class ProductCode(BaseModel):
    id: uuid.UUID
    promoCode: str | None


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

class Product(BaseModel):
    id: uuid.UUID
    title: str
    priceRubbles: int
    availabilityDurationDays: int | None
    usageCount: int | None
    description: str
    categoryIds: list[uuid.UUID]

class AdminProduct(Product):
    returnUrl: str
    promoCodes: list[PromoCode]

class NewPrice(BaseResponse):
    newPrice: int