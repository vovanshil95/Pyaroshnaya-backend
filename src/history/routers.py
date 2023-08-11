from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from auth.routes import get_access_token
from auth.utils import AccessTokenPayload
from database import get_async_session
from history.schemas import GptInteraction as GptInteractionSchema
from history.models import GptInteraction as GptInteractionModel
from questions.models import Answer, Question, Option

router = APIRouter(prefix='/history',
                   tags=['History'])

@router.get('/gptHisory')
async def get_history(user_token: AccessTokenPayload=Depends(get_access_token),
                       session: AsyncSession=Depends(get_async_session)) -> list[GptInteractionSchema]:
    print(stmt:=select(text('id'),
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
                            Question,
                            func.array_agg(Answer.text).label('question_answers'),
                            func.array_agg(Option.text).label('options'))
                   .join(Answer)
                   .join(Question)
                   .join(Option)
                   .where(Answer.user_id == user_token.id)
                   .group_by(Question.id)
                   .group_by(GptInteractionModel.id)
                   .select_from(GptInteractionModel)
                   .subquery(name='interaction'))
                .group_by(text('(interaction.id)'))
    )
    interactions = (await session.execute(stmt)).all()
    print(interactions)

    # list(map(lambda interaction: GptInteractionSchema(id=interaction[0]), interactions))

    return []