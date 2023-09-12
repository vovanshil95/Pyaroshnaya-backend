import datetime

from questions.schemas import QuestionAnswers
from utils import BaseResponse

class GptInteraction(QuestionAnswers):
    dateTime: datetime.datetime
    gptResponse: str
    isFavorite: bool

class HistoryResponse(BaseResponse):
    data: list[GptInteraction]
