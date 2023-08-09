from sqlalchemy import Column, String, UUID, TIMESTAMP, LargeBinary, Float
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID, primary_key=True)
    name = Column(String, unique=True)
    phone = Column(String, nullable=False, unique=True)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    balance = Column(Float, nullable=False)
    till_date = Column(TIMESTAMP)
    status = Column(String, nullable=False)
