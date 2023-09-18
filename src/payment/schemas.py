import uuid

from pydantic import BaseModel

from utils import BaseResponse


class Product(BaseModel):
    id: uuid.UUID


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
