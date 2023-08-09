import uuid

from pydantic import BaseModel

from utils import BaseResponse


class Category(BaseModel):
    def __init__(self, id: uuid.UUID,
                 title: str,
                 description: str = None,
                 parent_id: uuid.UUID = None,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.Id = id
        self.title = title
        self.Description = description
        self.ParentId = parent_id

    Id: uuid.UUID
    title: str
    Description: str
    ParentId: uuid.UUID

class CategoriesResponse(BaseResponse):
    categories: list[Category]

class Question(BaseModel):
    def __init__(self,
                 id: uuid.UUID,
                 question: str,
                 snippet: str,
                 options: list[str],
                 is_required: bool,
                 category_id: uuid.UUID,
                 answer: str=None,
                 answers: list[str]=None):
        self.Id = id
        self.Question = question
        self.Snippet = snippet
        self.Options = options
        self.Answer = answer
        self.Answers = answers
        self.IsRequired = is_required
        self.CategoryId = category_id

    Id: uuid.UUID
    Question: str
    Snippet: str
    Options: list[str]
    Answer: str | None
    Answers: str | None
    IsRequired: bool
    CategoryId: uuid.UUID

class QuestionsResponse(BaseResponse):
    questions: list[Question]

class CategoryId(BaseModel):
    categoryId: uuid.UUID
