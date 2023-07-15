from datetime import datetime
import uuid

from sqlalchemy import Column, LargeBinary, ForeignKey, UUID, TIMESTAMP, BOOLEAN, String

from users.models import Base

class Auth(Base):
    __tablename__ = 'auth'
    id = Column(UUID, primary_key=True)
    user_id = Column(ForeignKey('users.id', ondelete='cascade'), nullable=False)
    password = Column(LargeBinary, nullable=False)

class TokenGroup(Base):
    def __init__(self, id: uuid.UUID):
        self.id = id

    __tablename__ = 'token_group'
    id = Column(UUID, primary_key=True)

class RefreshToken(Base):
    def __init__(self,
                 id: uuid.UUID=None,
                 user_id: uuid.UUID=None,
                 user_agent: str=None,
                 exp: datetime=None,
                 valid: bool=None,
                 next_token: uuid.UUID=None,
                 last_use: datetime=None,
                 token_group_id: uuid.UUID=None):
        self.id = id if id else uuid.uuid4()
        self.user_id = user_id
        self.user_agent = user_agent
        self.till_date = till_date
        self.valid = valid
        self.next_token = next_token
        self.last_use = last_use
        self.token_group_id = token_group_id


    __tablename__ = 'refresh_token'
    id = Column(UUID, primary_key=True)
    user_id = Column(ForeignKey('users.id', ondelete='cascade'), nullable=False)
    user_agent = Column(String, nullable=False)
    till_date = Column(TIMESTAMP, nullable=False)
    valid = Column(BOOLEAN, nullable=False)
    next_token = Column(UUID)
    last_use = Column(TIMESTAMP)
    token_group_id = Column(ForeignKey('token_group.id', ondelete='cascade'), nullable=False)
