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
                 expandable: bool=True,
                 expanding: bool=False,
                 is_promo: bool=False,
                 categories_size: int | None=None,
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
        self.categories_size = categories_size
        self.expandable = expandable
        self.is_promo = is_promo
        self.expanding = expanding

    id = Column(UUID, primary_key=True)
    price_rubbles = Column(Integer, nullable=False)
    availability_duration_days = Column(Integer)
    usage_count = Column(Integer)
    description = Column(String, nullable=False)
    return_url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    active = Column(BOOLEAN, nullable=False)
    categories_size = Column(Integer)
    expandable = Column(BOOLEAN, nullable=False)
    is_promo = Column(BOOLEAN, nullable=False)
    expanding = Column(BOOLEAN, nullable=False)

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
    product_to_expend_id = Column(ForeignKey('product.id', ondelete='cascade'))

    def __init__(self,
                 id: uuid.UUID,
                 user_id: uuid.UUID,
                 product_id: uuid.UUID,
                 product_to_expend_id: uuid.UUID | None=None):
        UserProductMixin.__init__(self,
                                  user_id=user_id,
                                  product_id=product_id)
        self.id = id
        self.product_to_expend_id = product_to_expend_id

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

class PurchaseCategory(Base):
    __tablename__ = 'purchase_category'
    purchase_id = Column(ForeignKey('purchase.id', ondelete='cascade'), nullable=False, primary_key=True)
    category_id = Column(ForeignKey('question_category.id', ondelete='cascade'), nullable=False, primary_key=True)

    def __init__(self,
                 purchase_id: uuid.UUID,
                 category_id: uuid.UUID):
        self.purchase_id = purchase_id
        self.category_id = category_id

class PaymentCategory(Base):
    __tablename__ = 'payment_category'
    payment_id = Column(ForeignKey('payment.id', ondelete='cascade'), nullable=False, primary_key=True)
    category_id = Column(ForeignKey('question_category.id', ondelete='cascade'), nullable=False, primary_key=True)

    def __init__(self,
                 payment_id: uuid.UUID,
                 category_id: uuid.UUID):
        self.payment_id = payment_id
        self.category_id = category_id
