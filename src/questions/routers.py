import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth.routes import get_access_token
from auth.utils import AccessTokenPayload
from questions.models import Category as CategoryModel, Question, Answer, Option
from questions.schemas import Question as QuestionSchema
from questions.schemas import CategoriesResponse, QuestionsResponse, Category, CategoryId
from history.models import GptInteraction
from database import get_async_session
from utils import BaseResponse

router = APIRouter(prefix='/api/question',
                   tags=['Questions'])

QuestionsData = list[tuple[Question, list[str], list[uuid.UUID], list[str]]]

def get_gpt_response(questions: list[QuestionSchema]) -> str:
    return 'this is just test response not from gpt'

async def get_question_data(user_id: uuid.UUID, session: AsyncSession, category_id: uuid.UUID) -> QuestionsData:
    return (await session.execute(select(
            Question,
            func.array_agg(Answer.text),
            func.array_agg(Answer.id),
            func.array_agg(Option.text)
    ).group_by(Question.id)
     .where(and_(Answer.user_id == user_id,
                 Question.category_id==category_id,
                 Answer.interaction_id.is_(None))))).scalars().all()

def get_question_schemas(questions: QuestionsData) -> list[QuestionSchema]:
    return list(map(lambda question_data:
                    QuestionSchema(id=question_data[0].id,
                                   question=question_data[0].question_text,
                                   snippet=question_data[0].snippet,
                                   options=question_data[3]
                                   if len(question_data[3]) != 0 else None,
                                   is_required=question_data[0].is_required,
                                   category_id=question_data[0].category_id,
                                   answer=question_data[1][0]
                                   if len(question_data[1]) == 1 else None,
                                   answers=question_data[1]
                                   if len(question_data[1]) > 1 else None), questions))


@router.get('/categories', responses={200: {'model': CategoriesResponse},
                                           400: {'model': BaseResponse}})
async def get_categories(session: AsyncSession = Depends(get_async_session)) -> CategoriesResponse:
    return CategoriesResponse(message='status success',
                              categories=list(map(lambda category_model:
               Category(id=category_model.id,
                        title=category_model.title,
                        description=category_model.description,
                        parent_id=category_model.parent_id),
               (await session.execute(select(CategoryModel))).scalars().all())))

@router.get('/questions', responses={200: {'model': QuestionsResponse},
                                          400: {'model': BaseResponse},
                                          401: {'model': BaseResponse, 'description': 'User is not authorized'}})
async def get_questions(categoryId: uuid.UUID,
                        user_token: AccessTokenPayload=Depends(get_access_token),
                        session: AsyncSession=Depends(get_async_session)) -> QuestionsResponse:
    return QuestionsResponse(message='status success',
                             questions=get_question_schemas(await get_question_data(user_token.id,
                                                                                    session,
                                                                                    categoryId)))

@router.post('/response', responses={200: {'model': QuestionsResponse},
                                          400: {'model': BaseResponse, 'description': 'required fields not filled'},
                                          401: {'model': BaseResponse, 'description': 'User is not authorized'}})
async def gpt_response(category: CategoryId,
                       user_token: AccessTokenPayload=Depends(get_access_token),
                       session: AsyncSession=Depends(get_async_session)) -> list[QuestionSchema]:
    questions_data = await get_question_data(user_token.id, session, category.categoryId)
    questions = get_question_schemas(questions_data)
    for question in questions:
        if question.IsRequired and not question.Answers and not question.Answer:
            raise HTTPException(status_code=400, detail='required fields not filled')
    response = get_gpt_response(questions)

    interaction_id = uuid.uuid4()
    answer_ids = []

    session.add(GptInteraction(id=uuid.uuid4(),
                   user_id=user_token.id,
                   time_happened=datetime.now(),
                   response=response))

    for question_data in questions_data:
        answer_ids.extend(question_data[2])

    await session.flush()
    await session.execute(update(Answer).where(Answer.id.in_(answer_ids)).values(interaction_id=interaction_id))

    return questions
