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
from questions.schemas import Option as OptionShema
from utils import BaseResponse, IdSchema, try_uuid

router = APIRouter(prefix='/history',
                   tags=['History'])

async def get_history(session: AsyncSession, user_id: uuid.UUID, category_id: uuid.UUID) -> HistoryResponse:
    interactions = (await session.execute(
        a:=select(text('id'),
               text('time_happened'),
               text('response'),
               text('is_favorite'),
               text('array_agg(id_1)'),
               text('array_agg(question_text)'),
               text('array_agg(snippet)'),
               text('array_agg(option_ids)'),
               text('array_agg(option_texts)'),
               text('array_agg(question_answers)'),
               text('array_agg(is_required)'),
               text('category_id'))
        .select_from(select(GptInteractionModel,
                            QuestionModel,
                            func.string_agg(Answer.text.distinct(), 'DEL').label('question_answers'),
                            func.string_agg(text('option.id::text'), 'DEL').label('option_ids'),
                            func.string_agg(Option.option_text.distinct(), 'DEL').label('option_texts'))
                     .join(Answer)
                     .join(QuestionModel)
                     .join(Option, isouter=True)
                     .where(Answer.user_id == user_id)
                     .group_by(QuestionModel.id)
                     .group_by(GptInteractionModel.id)
                     .select_from(GptInteractionModel)
                     .subquery(name='interaction'))
        .where(text(f"interaction.category_id = '{category_id}'"))
        .group_by(text('(interaction.id)'))
        .group_by(text('interaction.time_happened'))
        .group_by(text('interaction.response'))
        .group_by(text('interaction.is_favorite'))
        .group_by(text('interaction.category_id')))).all()

    interactions = list(map(lambda interaction:
                            GptInteractionSchema(id=interaction[0],
                                                 userId=user_id,
                                                 dateTime=interaction[1],
                                                 gptResponse=interaction[2],
                                                 isFavorite=interaction[3],
                                                 questions=[QuestionSchema(
                                                     id=id,
                                                     question=interaction[5][i],
                                                     snippet=interaction[6][i],
                                                     options=[OptionShema(id=uuid.UUID(hex=id),text=text)
                                                              for id, text in zip(interaction[7][i].split('DEL'),
                                                                                  interaction[8][i].split('DEL'))]
                                                     if interaction[7][i] is not None else None,
                                                     answer=try_uuid(interaction[9][i][0])
                                                     if len(interaction[9][i].split('DEL')) == 1 else None,
                                                     answers=list(map(try_uuid, interaction[8][i].split('DEL')))
                                                     if len(interaction[9][i].split('DEL')) > 1 else None,
                                                     isRequired=interaction[10][i],
                                                     categoryId=interaction[11]
                                                 ) for i, id in enumerate(interaction[4])]), interactions))

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
async def get_history_route(categoryId: uuid.UUID,
                            user_token: AccessTokenPayload=Depends(get_access_token),
                            session: AsyncSession=Depends(get_async_session)) -> HistoryResponse:
    return await get_history(session=session, user_id=user_token.id, category_id=categoryId)
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
