from sqlalchemy import Column, String, UUID, TIMESTAMP, LargeBinary, Float
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable=False, unique=True)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    balance = Column(Float, nullable=False)
    till_date = Column(TIMESTAMP)

class UnverifiedUser(Base):
    __tablename__ = 'unverified_user'
    id = Column(UUID, primary_key=True)
    username = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    company = Column(String, nullable=False)
    last_sms_code = Column(String, nullable=False)
    last_sms_time = Column(TIMESTAMP, nullable=False)
    ip = Column(String, nullable=False)
    user_agent = Column(String, nullable=False)
    password = Column(LargeBinary, nullable=False)
