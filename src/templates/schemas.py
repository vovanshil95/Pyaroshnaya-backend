import uuid

from pydantic import BaseModel

from questions.schemas import QuestionAnswers
from utils import BaseResponse


class TemplatesResponse(BaseResponse):
    templates: list[QuestionAnswers]

class NewAnswer(BaseModel):
    quetionID: uuid.UUID
    answer: str | uuid.UUID | None

class NewAnswers(BaseModel):
    templateId: uuid.UUID
    newAnswers: list[NewAnswer]
