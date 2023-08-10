import uuid

from pydantic import BaseModel

from utils import BaseResponse


class Category(BaseModel):
    Id: uuid.UUID
    title: str
    Description: str | None
    ParentId: uuid.UUID | None

class CategoriesResponse(BaseResponse):
    categories: list[Category]

class Question(BaseModel):
    Id: uuid.UUID
    Question: str
    Snippet: str | None
    Options: list[str] | None
    Answer: str | None
    Answers: str | None
    IsRequired: bool
    CategoryId: uuid.UUID

class QuestionsResponse(BaseResponse):
    questions: list[Question]

class CategoryId(BaseModel):
    categoryId: uuid.UUID
