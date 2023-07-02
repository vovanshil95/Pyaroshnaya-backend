from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, UUID

from users.models import Base

class Auth(Base):
    __tablename__ = 'auth'
    id = Column(UUID, primary_key=True)
    user_id = Column(ForeignKey('users.id', ondelete='cascade'), nullable=False)
    password = Column(String, nullable=False)
