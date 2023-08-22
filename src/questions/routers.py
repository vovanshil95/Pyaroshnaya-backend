import uuid
from datetime import datetime
from typing import Callable

import openai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_, update, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from auth.routes import get_access_token
from auth.utils import AccessTokenPayload
from questions.models import Category as CategoryModel, Option, Prompt
from questions.models import Answer as AnswerModel
from questions.models import Question as QuestionModel
from questions.schemas import Question as QuestionSchema, GptAnswerResponse
from questions.schemas import Category as CategorySchema
from questions.schemas import Answer as AnswerSchema
from questions.schemas import CategoriesResponse, QuestionsResponse, CategoryId
from history.models import GptInteraction
from database import get_async_session
from utils import BaseResponse

router = APIRouter(prefix='/question',
                   tags=['Questions'])

QuestionsData = list[tuple[QuestionModel, list[str], list[str], list[uuid.UUID]]]

def get_gpt_send():
    def get_gpt_response(answers: list[str], prompt: list[str]) -> str:

        answers = list(map(lambda ans: '' if ans is None else ans, answers))

        answers.insert(0, None)

        filled_prompt = '\n'.join(prompt).format(*answers)

        response = openai.ChatCompletion.create(model='gpt-4',
                                                messages=[{'role': 'user', 'content': filled_prompt}])
        response = response['choices'][0]['message']['content']
        print(filled_prompt)

        return response

    return get_gpt_response

async def get_question_data(user_id: uuid.UUID, session: AsyncSession, category_id: uuid.UUID) -> QuestionsData:
    questions = (await session.execute(select(QuestionModel,
                                              func.array_agg(AnswerModel.text),
                                              func.array_agg(Option.text),
                                              func.array_agg(AnswerModel.id))
                                       .join(AnswerModel, isouter=True)
                                       .join(Option, isouter=True)
                                       .where(and_(QuestionModel.category_id==category_id,
                                                   AnswerModel.interaction_id.is_(None),
                                                   or_(AnswerModel.user_id==user_id,
                                                       AnswerModel.id.is_(None))))
                                       .group_by(QuestionModel.id)
                                       .order_by(QuestionModel.order_index))).all()
    questions = list(map(lambda q: (q[0],
                                    list(filter(lambda ans: ans is not None, q[1])),
                                    list(filter(lambda opt: opt is not None, q[2])),
                                    list(filter(lambda opt: opt is not None, q[3]))), questions))
    return questions

def get_question_schemas(questions: QuestionsData) -> list[QuestionSchema]:
    return list(map(lambda question_data:
                    QuestionSchema(id=question_data[0].id,
                                   question=question_data[0].question_text,
                                   snippet=question_data[0].snippet,
                                   options=question_data[2]
                                   if len(question_data[2]) != 0 else None,
                                   isRequired=question_data[0].is_required,
                                   categoryId=question_data[0].category_id,
                                   answer=question_data[1][0]
                                   if len(question_data[1]) == 1 else None,
                                   answers=question_data[1]
                                   if len(question_data[1]) > 1 else None), questions))


@router.get('/categories',
            dependencies=[Depends(get_access_token)],
            responses={200: {'model': CategoriesResponse},
                       400: {'model': BaseResponse}})
async def get_categories(session: AsyncSession = Depends(get_async_session)) -> CategoriesResponse:
    return CategoriesResponse(message='status success',
                              categories=list(map(lambda category_model:
               CategorySchema(id=category_model.id,
                              title=category_model.title,
                              description=category_model.description,
                              parentId=category_model.parent_id,
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

@router.post('/response', responses={200: {'model': GptAnswerResponse},
                                          400: {'model': BaseResponse, 'description': 'required fields not filled'},
                                          401: {'model': BaseResponse, 'description': 'User is not authorized'}})
async def gpt_response(category: CategoryId,
                       user_token: AccessTokenPayload=Depends(get_access_token),
                       session: AsyncSession=Depends(get_async_session),
                       gpt_send: Callable=Depends(get_gpt_send)) -> GptAnswerResponse:
    questions_data = await get_question_data(user_token.id, session, category.categoryId)
    questions = get_question_schemas(questions_data)
    for question in questions:
        if question.isRequired and not question.answers and not question.answer:
            raise HTTPException(status_code=400, detail='required fields not filled')

    prompt = (await session.execute(select(Prompt.text)
                                    .where(Prompt.category_id == category.categoryId)
                                    .order_by(Prompt.order_index))).scalars().all()

    answers = list(map(lambda q: q.answer, questions))

    response = gpt_send(answers, prompt)

    interaction_id = uuid.uuid4()
    answer_ids = []

    session.add(GptInteraction(id=interaction_id,
                               time_happened=datetime.now(),
                               response=response))

    for question_data in questions_data:
        answer_ids.extend(question_data[3])

    await session.flush()
    await session.execute(update(AnswerModel).where(AnswerModel.id.in_(answer_ids)).values(interaction_id=interaction_id))

    return GptAnswerResponse(message='status success',
                             questions=questions,
                             gptResponse=response)

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
