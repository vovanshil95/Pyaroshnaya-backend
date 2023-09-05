import datetime
import uuid

from pydantic import BaseModel

from utils import BaseResponse


class Category(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    parentId: uuid.UUID | None
    isMainScreenPresented: bool
    isCategoryScreenPresented: bool
    orderIndex: str

class CategoriesResponse(BaseResponse):
    categories: list[Category]

class Option(BaseModel):
    id: uuid.UUID
    text: str

class Question(BaseModel):
    id: uuid.UUID
    question: str
    snippet: str | None
    options: list[Option] | None
    answer: str | uuid.UUID | None
    answers: list[str] | list[uuid.UUID] | None
    isRequired: bool
    categoryId: uuid.UUID
    questionType: str = 'text'

class QuestionsResponse(BaseResponse):
    questions: list[Question]

class GptAnswerResponse(QuestionsResponse):
    answerId: uuid.UUID
    dateTime: datetime.datetime
    gptResponse: str

class PromptResponse(BaseResponse):
    questions: list[Question]
    filledPrompt: str

class CategoryId(BaseModel):
    categoryId: uuid.UUID

class Answer(BaseModel):
    questionId: uuid.UUID
    answer: str | None
    answers: list[str] | None
