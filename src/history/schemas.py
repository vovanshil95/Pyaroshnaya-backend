import datetime
import uuid

from pydantic import BaseModel

from questions.schemas import Question
from utils import BaseResponse


class GptInteraction(BaseModel):
    id: uuid.UUID
    userId: uuid.UUID
    questions: list[Question]
    dateTime: datetime.datetime
    gptResponse: str
    isFavorite: bool

class HistoryResponse(BaseResponse):
    data: list[GptInteraction]