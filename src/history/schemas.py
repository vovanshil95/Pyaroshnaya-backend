import datetime
import uuid

from pydantic import BaseModel

from questions.schemas import Question
from utils import BaseResponse


class GptInteraction(BaseModel):
    Id: uuid.UUID
    user_id: uuid.UUID
    Questions: list[Question]
    dateTime: datetime.datetime
    gptResponse: str
    isFavorite: bool

class HistoryResponse(BaseResponse):
    data: list[GptInteraction]