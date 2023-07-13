from sqlalchemy import Column, String, UUID, TIMESTAMP
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    company = Column(String, nullable=False)

class UnverifiedUser(Base):
    __tablename__ = 'unverified_user'
    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    company = Column(String, nullable=False)
    last_sms_time = Column(TIMESTAMP, nullable=False)
    ip = Column(String, nullable=False)
    user_agent = Column(String, nullable=False)