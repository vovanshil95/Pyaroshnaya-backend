from datetime import datetime
import uuid

from sqlalchemy import Column, LargeBinary, ForeignKey, UUID, TIMESTAMP, BOOLEAN, String

from users.models import Base

class Auth(Base):
    __tablename__ = 'auth'
    id = Column(UUID, primary_key=True)
    user_id = Column(ForeignKey('users.id', ondelete='cascade'), nullable=False)
    password = Column(LargeBinary, nullable=False)



class SmsSend(Base):
    __tablename__ = 'sms_send'
    user_id = Column(ForeignKey('users.id', ondelete='cascade'), nullable=False)
    ip = Column(String, primary_key=True)
    user_agent = Column(String, nullable=False)
    time_send = Column(TIMESTAMP, nullable=False)

class RefreshToken(Base):
    def __init__(self,
                 id: uuid.UUID=None,
                 user_id: uuid.UUID=None,
                 user_agent: str=None,
                 exp: datetime=None,
                 last_use: datetime=None,
                 theme: str='LIGHT_THEME'):
        self.id = id if id else uuid.uuid4()
        self.user_id = user_id
        self.user_agent = user_agent
        self.theme = theme
        self.exp = exp
        self.last_use = last_use


    __tablename__ = 'refresh_token'
    id = Column(UUID, primary_key=True)
    user_id = Column(ForeignKey('users.id', ondelete='cascade'), nullable=False)
    user_agent = Column(String, nullable=False)
    exp = Column(TIMESTAMP, nullable=False)
    last_use = Column(TIMESTAMP)
    theme = Column(String, nullable=False, default='LIGHT_THEME')
