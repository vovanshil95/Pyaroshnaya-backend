import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from auth.routes import get_access_token
from auth.utils import AccessTokenPayload
from database import get_async_session
from history.schemas import GptInteraction as GptInteractionSchema, HistoryResponse
from history.models import GptInteraction as GptInteractionModel
from questions.models import Answer, Option
from questions.models import Question as QuestionModel
from questions.schemas import Question as QuestionSchema
from utils import BaseResponse, IdSchema

router = APIRouter(prefix='/history',
                   tags=['History'])

async def get_history(session: AsyncSession, user_id: uuid.UUID) -> HistoryResponse:
    interactions = (await session.execute(
        select(text('id'),
               text('array_agg(user_id)'),
               text('array_agg(time_happened)'),
               text('array_agg(response)'),
               text('array_agg(is_favorite)'),
               text('array_agg(id_1)'),
               text('array_agg(question_text)'),
               text('array_agg(snippet)'),
               text('array_agg(options)'),
               text('array_agg(question_answers)'),
               text('array_agg(is_required)'),
               text('array_agg(category_id)'))
        .select_from(select(GptInteractionModel,
                            QuestionModel,
                            func.array_agg(Answer.text).label('question_answers'),
                            func.array_agg(Answer.user_id).label('user_id'),
                            func.array_agg(Option.text).label('options'))
                     .join(Answer)
                     .join(QuestionModel)
                     .join(Option, isouter=True)
                     .where(Answer.user_id == user_id)
                     .group_by(QuestionModel.id)
                     .group_by(GptInteractionModel.id)
                     .select_from(GptInteractionModel)
                     .subquery(name='interaction'))
        .group_by(text('(interaction.id)')))).all()

    interactions = list(map(lambda interaction:
                            GptInteractionSchema(Id=interaction[0],
                                                 userId=interaction[1][0][0],
                                                 dateTime=interaction[2][0],
                                                 gptResponse=interaction[3][0],
                                                 isFavorite=interaction[4][0],
                                                 Questions=[QuestionSchema(
                                                     Id=id,
                                                     Question=interaction[6][i],
                                                     Snippet=interaction[7][i],
                                                     Options=interaction[8][i] if interaction[8][i] != [None] else None,
                                                     Answer=interaction[9][i][0] if len(
                                                         interaction[9][i]) == 1 else None,
                                                     Answers=interaction[9][i] if len(interaction[9][i]) > 1 else None,
                                                     IsRequired=interaction[10][i],
                                                     CategoryId=interaction[11][i]
                                                 ) for i, id in enumerate(interaction[5])]), interactions))

    return HistoryResponse(message='status success', data=interactions)

async def switch_favorite(session: AsyncSession,
                          user_id: uuid.UUID,
                          interaction_id: uuid.UUID,
                          to_favorite: bool = True) -> HistoryResponse:
    if (interaction := await session.get(GptInteractionModel, interaction_id)) is None:
        raise HTTPException(status_code=404, detail='History entity with this id doesnt exist')

    interaction.is_favorite = to_favorite
    session.add(interaction)
    session.add(interaction)
    await session.flush()

    return await get_history(session=session, user_id=user_id)

@router.get('/gptHistory', responses={200: {'model': HistoryResponse},
                                           300: {'model': BaseResponse, 'description': 'user is blocked'},
                                           400: {'model': BaseResponse, 'description': 'error: User-Agent required'},
                                           401: {'model': BaseResponse, 'description': 'user is not authorized'},
                                           498: {'model': BaseResponse, 'description': 'the access token is invalid'}})
async def get_history_route(user_token: AccessTokenPayload=Depends(get_access_token),
                      session: AsyncSession=Depends(get_async_session)) -> HistoryResponse:
    return await get_history(session=session, user_id=user_token.id)
@router.post('/gptHistoryFavorite', responses={200: {'model': HistoryResponse},
                                                    300: {'model': BaseResponse, 'description': 'user is blocked'},
                                                    400: {'model': BaseResponse, 'description': 'error: User-Agent required'},
                                                    401: {'model': BaseResponse, 'description': 'user is not authorized'},
                                                    404: {'model': BaseResponse, 'description': 'History entity with this id doesnt exist'},
                                                    498: {'model': BaseResponse, 'description': 'the access token is invalid'}})
async def add_to_favorite(id_schema: IdSchema,
                          user_token: AccessTokenPayload=Depends(get_access_token),
                          session: AsyncSession=Depends(get_async_session)) -> HistoryResponse:
    return await switch_favorite(session=session,
                                 user_id=user_token.id,
                                 interaction_id=id_schema.id,
                                 to_favorite=True)

@router.delete('/gptHistoryFavorite', responses={200: {'model': HistoryResponse},
                                                      300: {'model': BaseResponse, 'description': 'user is blocked'},
                                                      400: {'model': BaseResponse, 'description': 'error: User-Agent required'},
                                                      401: {'model': BaseResponse, 'description': 'user is not authorized'},
                                                      404: {'model': BaseResponse, 'description': 'History entity with this id doesnt exist'},
                                                      498: {'model': BaseResponse, 'description': 'the access token is invalid'}})
async def delete_from_favorite(id: uuid.UUID,
                               user_token: AccessTokenPayload=Depends(get_access_token),
                               session: AsyncSession=Depends(get_async_session)) -> HistoryResponse:
    return await switch_favorite(session=session,
                                 user_id=user_token.id,
                                 interaction_id=id,
                                 to_favorite=False)
