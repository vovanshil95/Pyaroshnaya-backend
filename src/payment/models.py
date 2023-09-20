import datetime
import uuid

from sqlalchemy import Column, UUID, Integer, String, ForeignKey, TIMESTAMP, BOOLEAN

from questions.models import Base

class Product(Base):
    __tablename__ = 'product'

    def __init__(self,
                 id: uuid.UUID,
                 price_rubbles: int,
                 description: str,
                 return_url: str,
                 title: str,
                 active: bool=True,
                 availability_duration_days: int | None=None,
                 usage_count: int | None=None):
        self.id = id
        self.price_rubbles = price_rubbles
        self.title = title
        self.availability_duration_days = availability_duration_days
        self.usage_count = usage_count
        self.description = description
        self.return_url = return_url
        self.active = active

    id = Column(UUID, primary_key=True)
    price_rubbles = Column(Integer, nullable=False)
    availability_duration_days = Column(Integer)
    usage_count = Column(Integer)
    description = Column(String, nullable=False)
    return_url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    active = Column(BOOLEAN, nullable=False)

class UserProductMixin:
    def __init__(self,
                 user_id: uuid.UUID,
                 product_id: uuid.UUID):
        self.user_id = user_id
        self.product_id = product_id
    user_id = Column(ForeignKey('users.id', ondelete='cascade'), nullable=False)
    product_id = Column(UUID, ForeignKey('product.id', ondelete='cascade'))

class Purchase(Base, UserProductMixin):
    __tablename__ = 'purchase'
    id = Column(UUID, primary_key=True)
    expiration_time = Column(TIMESTAMP)
    remaining_uses = Column(Integer)

    def __init__(self,
                 id: uuid.UUID,
                 user_id: uuid.UUID,
                 product_id: uuid.UUID,
                 expiration_time: datetime.datetime,
                 remaining_uses: int):
        UserProductMixin.__init__(self,
                                  user_id=user_id,
                                  product_id=product_id)
        self.id = id
        self.expiration_time = expiration_time
        self.remaining_uses = remaining_uses

class Payment(Base, UserProductMixin):
    __tablename__ = 'payment'
    id = Column(UUID, primary_key=True)

    def __init__(self,
                 id: uuid.UUID,
                 user_id: uuid.UUID,
                 product_id: uuid.UUID):
        UserProductMixin.__init__(self,
                                  user_id=user_id,
                                  product_id=product_id)
        self.id = id

class PromoCode(Base):
    __tablename__ = 'promo_code'
    id = Column(UUID, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    discount_absolute = Column(Integer)
    discount_percent = Column(Integer)
    product_id = Column(ForeignKey('product.id', ondelete='cascade'), nullable=False)

    def __init__(self,
                 id: uuid.UUID,
                 code: str,
                 product_id: uuid.UUID,
                 discount_absolute: int=None,
                 discount_percent: int=None):
        self.id = id
        self.code = code
        self.product_id = product_id
        self.discount_absolute = discount_absolute
        self.discount_percent = discount_percent

class ProductCategory(Base):
    __tablename__ = 'product_category'
    product_id = Column(ForeignKey('product.id', ondelete='cascade'), nullable=False, primary_key=True)
    category_id = Column(ForeignKey('question_category.id', ondelete='cascade'), nullable=False, primary_key=True)

    def __init__(self,
                 product_id: uuid.UUID,
                 category_id: uuid.UUID):
        self.product_id = product_id
        self.category_id = category_id
