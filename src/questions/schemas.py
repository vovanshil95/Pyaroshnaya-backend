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

class FullOption(Option):
    text_to_prompt: str

class BaseQuestion(BaseModel):
    id: uuid.UUID
    question: str
    snippet: str | None
    options: list[FullOption] | None
    isRequired: bool
    categoryId: uuid.UUID
    questionType: str = 'text'

class AdminQuestion(BaseQuestion):
    orderIndex: int

class Question(BaseQuestion):
    answer: str | uuid.UUID | None
    answers: list[str] | list[uuid.UUID] | None
    options: list[Option] | None

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

class AdminQuestionsResponse(BaseResponse):
    questions: list[AdminQuestion]

class Prompt(BaseModel):
    categoryId: uuid.UUID
    prompt: list[str]

class AdminCategory(Category):
    prompt: list[str]

class AdminCategoriesResponse(BaseResponse):
    categories: list[AdminCategory]

class UnfilledPromptResponse(BaseResponse):
    prompt: list[str]