import uuid

from sqlalchemy import Column, UUID, ForeignKey, String

from history.models import Base

class Template(Base):
    __tablename__ = 'template'
    def __init__(self, id: uuid.UUID, user_id: uuid.UUID, title: str):
        self.id = id
        self.user_id = user_id
        self.title = title

    id = Column(UUID, primary_key=True)
    user_id = Column(ForeignKey('users.id', ondelete='cascade'))
    title = Column(String, nullable=False)
