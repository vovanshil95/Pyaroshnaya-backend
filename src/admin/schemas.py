from payment.schemas import AdminProduct, Product
from utils import BaseResponse

class AdminProductsResponse(BaseResponse):
    data: list[AdminProduct]

class ProductsResponse(BaseResponse):
    data: list[Product]
