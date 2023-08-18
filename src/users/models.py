import datetime
import uuid

from sqlalchemy import Column, String, UUID, TIMESTAMP, Float, Integer
from database import Base

class User(Base):
    def __init__(self,
                 id: uuid.UUID,
                 chat_id: int,
                 name: str,
                 theme: str='LIGHT_THEME',
                 role: str='user',
                 balance: int=0,
                 company: str | None = None,
                 till_date: datetime.datetime | None=None):
        self.id = id
        self.chat_id = chat_id
        self.name = name
        self.company = company
        self.role = role
        self.balance = balance
        self.till_date = till_date
        self.theme = theme

    __tablename__ = 'users'
    id = Column(UUID, primary_key=True)
    chat_id = Column(Integer, nullable=False, unique=True)
    name = Column(String, unique=True)
    company = Column(String)
    role = Column(String, nullable=False)
    balance = Column(Float, nullable=False)
    till_date = Column(TIMESTAMP)
    theme = Column(String, nullable=False)
