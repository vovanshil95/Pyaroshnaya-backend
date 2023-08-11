from datetime import datetime
import uuid

from sqlalchemy import Column, TIMESTAMP, UUID, String, BOOLEAN

from auth.models import Base

class GptInteraction(Base):
    __tablename__ = 'gpt_interaction'
    def __init__(self, id: uuid.UUID, time_happened: datetime, response: str, is_favorite=False):
        self.id = id
        self.time_happened = time_happened
        self.response = response
        self.is_favorite = is_favorite

    id = Column(UUID, primary_key=True)
    time_happened = Column(TIMESTAMP, nullable=False)
    response = Column(String, nullable=False)
    is_favorite = Column(BOOLEAN, nullable=False, default=False)
