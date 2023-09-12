import uuid

from sqlalchemy import Column, UUID, ForeignKey

from history.models import Base

class Template(Base):
    __tablename__ = 'template'
    def __init__(self, id: uuid.UUID, user_id: uuid.UUID):
        self.id = id
        self.user_id = user_id

    id = Column(UUID, primary_key=True)
    user_id = Column(ForeignKey('users.id', ondelete='cascade'))
