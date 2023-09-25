import datetime
import uuid

from pydantic import BaseModel

from questions.schemas import QuestionAnswers
from utils import BaseResponse

class GptInteraction(QuestionAnswers):
    dateTime: datetime.datetime
    gptResponse: str
    isFavorite: bool

class UserHistory(BaseModel):
    history: list[GptInteraction]
    user_id: uuid.UUID

class UsersHistoryResponse(BaseResponse):
    data: list[UserHistory]


class HistoryResponse(BaseResponse):
    data: list[GptInteraction]
