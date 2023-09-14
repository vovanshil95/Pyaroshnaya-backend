import uuid

from pydantic import BaseModel

from questions.schemas import QuestionAnswers
from utils import BaseResponse


class Template(QuestionAnswers):
    title: str

class TemplatesResponse(BaseResponse):
    templates: list[Template]

class NewAnswer(BaseModel):
    quetionId: uuid.UUID
    answer: str | uuid.UUID | None

class NewTemplate(BaseModel):
    templateId: uuid.UUID
    title: str
    newAnswers: list[NewAnswer]

class NewTemplateSave(BaseModel):
    categoryId: uuid.UUID
    title: str