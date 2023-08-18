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

class Question(BaseModel):
    id: uuid.UUID
    question: str
    snippet: str | None
    options: list[str] | None
    answer: str | None
    answers: list[str] | None
    isRequired: bool
    categoryId: uuid.UUID

class QuestionsResponse(BaseResponse):
    questions: list[Question]

class CategoryId(BaseModel):
    categoryId: uuid.UUID

class Answer(BaseModel):
    questionId: uuid.UUID
    answer: str | None
    answers: list[str] | None
