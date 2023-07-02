from sqlalchemy import Column, String, UUID
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
