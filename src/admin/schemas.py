from payment.schemas import Product
from utils import BaseResponse

class ProductsResponse(BaseResponse):
    data: list[Product]