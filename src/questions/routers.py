import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_, update, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from auth.routes import get_access_token
from auth.utils import AccessTokenPayload
from questions.models import Category as CategoryModel, Option
from questions.models import Answer as AnswerModel
from questions.models import Question as QuestionModel
from questions.schemas import Question as QuestionSchema
from questions.schemas import Category as CategorySchema
from questions.schemas import Answer as AnswerSchema
from questions.schemas import CategoriesResponse, QuestionsResponse, CategoryId
from history.models import GptInteraction
from database import get_async_session
from utils import BaseResponse

router = APIRouter(prefix='/question',
                   tags=['Questions'])

QuestionsData = list[tuple[QuestionModel, list[str], list[str], list[uuid.UUID]]]

def get_gpt_response(questions: list[QuestionSchema]) -> str:
    return 'this is just test response not from gpt'

async def get_question_data(user_id: uuid.UUID, session: AsyncSession, category_id: uuid.UUID) -> QuestionsData:
    questions = (await session.execute(select(QuestionModel,
                                              func.array_agg(AnswerModel.text),
                                              func.array_agg(Option.text),
                                              func.array_agg(AnswerModel.id))
                                       .join(AnswerModel, isouter=True)
                                       .join(Option, isouter=True)
                                       .where(and_(QuestionModel.category_id==category_id,
                                                   or_(AnswerModel.user_id==user_id,
                                                       AnswerModel.id.is_(None))))
                                       .group_by(QuestionModel.id))).all()
    questions = list(map(lambda q: (q[0],
                                    list(filter(lambda ans: ans is not None, q[1])),
                                    list(filter(lambda opt: opt is not None, q[2])),
                                    list(filter(lambda opt: opt is not None, q[3]))), questions))
    return questions

def get_question_schemas(questions: QuestionsData) -> list[QuestionSchema]:
    return list(map(lambda question_data:
                    QuestionSchema(Id=question_data[0].id,
                                   Question=question_data[0].question_text,
                                   Snippet=question_data[0].snippet,
                                   Options=question_data[2]
                                   if len(question_data[2]) != 0 else None,
                                   IsRequired=question_data[0].is_required,
                                   CategoryId=question_data[0].category_id,
                                   Answer=question_data[1][0]
                                   if len(question_data[1]) == 1 else None,
                                   Answers=question_data[1]
                                   if len(question_data[1]) > 1 else None), questions))


@router.get('/categories', responses={200: {'model': CategoriesResponse},
                                           400: {'model': BaseResponse}})
async def get_categories(session: AsyncSession = Depends(get_async_session)) -> CategoriesResponse:
    return CategoriesResponse(message='status success',
                              categories=list(map(lambda category_model:
               CategorySchema(Id=category_model.id,
                              title=category_model.title,
                              Description=category_model.description,
                              ParentId=category_model.parent_id,
                              isMainScreenPresented=category_model.is_main_screen_presented,
                              isCategoryScreenPresented=category_model.is_category_screen_presented,
                              orderIndex=category_model.order_index
                              ),
               (await session.execute(select(CategoryModel)
                                      .order_by(CategoryModel.order_index))).scalars().all())))

@router.get('/questions', responses={200: {'model': QuestionsResponse},
                                          400: {'model': BaseResponse},
                                          401: {'model': BaseResponse, 'description': 'User is not authorized'},
                                          498: {'model': BaseResponse, 'description': 'the access token is invalid'}})
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

    session.add(GptInteraction(id=interaction_id,
                               time_happened=datetime.now(),
                               response=response))

    for question_data in questions_data:
        answer_ids.extend(question_data[3])

    await session.flush()
    await session.execute(update(AnswerModel).where(AnswerModel.id.in_(answer_ids)).values(interaction_id=interaction_id))

    return questions

@router.post('/questions', responses={200: {'model': QuestionsResponse},
                                           401: {'model': BaseResponse, 'description': 'User is not authorized'},
                                           404: {'model': BaseResponse, 'description': 'Question with this id doesnt exist'},
                                           422: {'model': BaseResponse, 'description': 'Validation error: answer or answers must be specified'},
                                           498: {'model': BaseResponse, 'description': 'the access token is invalid'}})
async def answer(answer: AnswerSchema,
                 user_token: AccessTokenPayload=Depends(get_access_token),
                 session: AsyncSession=Depends(get_async_session)) -> QuestionsResponse:

    if (question := await session.get(QuestionModel, answer.questionId)) is None:
        raise HTTPException(404, 'Question with this id doesnt exist')

    if (answer.answer is None and answer.answers is None or
        answer.answer is not None and answer.answers is not None):
        raise HTTPException(422, 'Validation error answer or answers must be specified')
    if answer.answers is None:
        if (answer_model := (await session.execute(
                select(AnswerModel)
                .where(and_(AnswerModel.question_id == answer.questionId,
                            AnswerModel.user_id == user_token.id,
                            AnswerModel.interaction_id.is_(None)))
        )).scalars().first()) is None:
            answer_model = AnswerModel(id=uuid.uuid4(),
                                       question_id=answer.questionId,
                                       text='',
                                       user_id=user_token.id)
        answer_model.text = answer.answer
        session.add(answer_model)
    else:
        await session.execute(delete(AnswerModel).where(and_(
            AnswerModel.question_id == answer.questionId,
            AnswerModel.user_id == user_token.id,
            AnswerModel.interaction_id.is_(None)
        )))
        await session.flush()
        session.add_all(list(map(lambda a:
                                 AnswerModel(id=uuid.uuid4(),
                                             question_id=answer.questionId,
                                             text=a,
                                             user_id=user_token.id),
                                 answer.answers)))
        await session.flush()
    return QuestionsResponse(message='status success',
                             questions=get_question_schemas(
                                 await get_question_data(user_id=user_token.id,
                                                         session=session,
                                                         category_id=question.category_id
                                                        )))
