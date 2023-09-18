import datetime
import uuid

from sqlalchemy import Column, UUID, Integer, String, ForeignKey, TIMESTAMP

from questions.models import Base

class Product(Base):
    __tablename__ = 'product'

    def __init__(self,
                 id: uuid.UUID,
                 price_rubbles: int,
                 description: str,
                 return_url: str,
                 availability_duration_days: int | None=None,
                 usage_count: int | None=None):
        self.id = id
        self.price_rubbles = price_rubbles
        self.availability_duration_days = availability_duration_days
        self.usage_count = usage_count
        self.description = description
        self.return_url = return_url

    id = Column(UUID, primary_key=True)
    price_rubbles = Column(Integer, nullable=False)
    availability_duration_days = Column(Integer)
    usage_count = Column(Integer)
    description = Column(String, nullable=False)
    return_url = Column(String, nullable=False)

class UserProductMixin:
    def __init__(self,
                 user_id: uuid.UUID,
                 product_id: uuid.UUID):
        self.user_id = user_id
        self.product_id = product_id
    user_id = Column(ForeignKey('users.id', ondelete='cascade'), nullable=False)
    product_id = Column(UUID, ForeignKey('product.id', ondelete='set null'))

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
