import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from auth.routes import get_access_token
from auth.utils import AccessTokenPayload
from database import get_async_session
from questions.schemas import QuestionAnswers
from questions.models import Answer
from questions.models import Option as OptionModel
from questions.schemas import Option as OptionSchema
from questions.models import Question as QuestionModel
from questions.schemas import Question as QuestionSchema
from questions.schemas import CategoryId
from templates.models import Template
from templates.schemas import TemplatesResponse, NewAnswers
from utils import try_uuid

router = APIRouter(prefix='/templates', tags=['Templates'])

async def get_templates_response(session: AsyncSession,
                                 user_id: uuid.UUID) -> TemplatesResponse:
    templates = (await session.execute(
        select(text('id'),
               text('array_agg(id_1)'),
               text('array_agg(question_text)'),
               text('array_agg(snippet)'),
               text('array_agg(option_ids)'),
               text('array_agg(option_texts)'),
               text('array_agg(question_answers)'),
               text('array_agg(is_required)'),
               text('category_id'))
        .select_from(select(Template,
                            QuestionModel,
                            func.string_agg(Answer.text.distinct(), 'DEL').label('question_answers'),
                            func.string_agg(text('option.id::text'), 'DEL').label('option_ids'),
                            func.string_agg(OptionModel.option_text.distinct(), 'DEL').label('option_texts'))
                     .join(Answer)
                     .join(QuestionModel)
                     .join(OptionModel, isouter=True)
                     .where(Answer.user_id == user_id)
                     .group_by(QuestionModel.id)
                     .group_by(Template.id)
                     .select_from(Template)
                     .subquery(name='template'))
        .group_by(text('template.id'))
        .group_by(text('template.category_id')))).all()

    templates = list(map(lambda template:
                            QuestionAnswers(id=template[0],
                                            userId=user_id,
                                            questions=[QuestionSchema(
                                                id=id,
                                                question=template[2][i],
                                                snippet=template[3][i],
                                                options=[OptionSchema(id=uuid.UUID(hex=id),text=text)
                                                         for id, text in zip(template[4][i].split('DEL'),
                                                                             template[5][i].split('DEL'))]
                                                if template[4][i] is not None else None,
                                                answer=try_uuid(template[6][i])
                                                if template[6][i] is not None and
                                                   len(template[6][i].split('DEL')) == 1 else None,
                                                answers=list(map(try_uuid, template[6][i].split('DEL')))
                                                if template[6][i] is not None and
                                                   len(template[6][i].split('DEL')) > 1 else None,
                                                isRequired=template[7][i],
                                                categoryId=template[8]
                                            ) for i, id in enumerate(template[1])]), templates))

    return TemplatesResponse(message='status success', templates=templates)

@router.put('')
async def add_template(category_id: CategoryId,
                       user_token: AccessTokenPayload=Depends(get_access_token),
                       session: AsyncSession=Depends(get_async_session)) -> TemplatesResponse:
    session.add(Template(id=(template_id := uuid.uuid4()),
                         user_id=user_token.id))
    await session.flush()
    question_ids = (await session.execute(
        select(QuestionModel.id)
        .where(QuestionModel.category_id == category_id.categoryId)
    )).scalars().all()

    answers = (await session.execute(
        select(Answer)
        .where(and_(Answer.user_id == user_token.id,
                    Answer.question_id.in_(question_ids),
                    Answer.interaction_id.is_(None),
                    Answer.template_id.is_(None))))
               ).scalars().all()

    new_answers = [Answer(id=uuid.uuid4(),
                          question_id=answer.question_id,
                          user_id=answer.user_id,
                          text=answer.text) for answer in answers]
    for answer in answers:
        answer.template_id = template_id

    session.add_all(answers)
    session.add_all(new_answers)
    await session.flush()

    return await get_templates_response(session=session,
                                        user_id=user_token.id)

@router.get('')
async def get_templates(user_token: AccessTokenPayload=Depends(get_access_token),
                        session: AsyncSession=Depends(get_async_session)) -> TemplatesResponse:
    return await get_templates_response(session=session,
                                        user_id=user_token.id)

@router.delete('')
async def delete_template(templateId: uuid.UUID,
                          user_token: AccessTokenPayload=Depends(get_access_token),
                          session: AsyncSession=Depends(get_async_session)) -> TemplatesResponse:
    template = await session.get(Template, templateId)
    if template.user_id != user_token.id:
        raise HTTPException(status_code=403, detail="can't delete foreign template")
    await session.delete(template)
    await session.flush()
    return await get_templates_response(session=session,
                                        user_id=user_token.id)

@router.post('')
async def change_template(answers: NewAnswers,
                          user_token: AccessTokenPayload=Depends(get_access_token),
                          session: AsyncSession=Depends(get_async_session)) -> TemplatesResponse:
    old_answers = (await session.execute(
        select(Answer)
        .where(
            and_(Answer.user_id == user_token.id,
                 Answer.template_id == answers.templateId)
        )
    )).scalars().all()

    old_answers = {old_answer.question_id: old_answer for old_answer in old_answers}
    changed_answers = []

    for new_answer in answers.newAnswers:
        answer = old_answers.get(new_answer.quetionId)
        if answer is None:
            raise HTTPException(status_code=404, detail=f"can't find question with id {new_answer.quetionId}")
        answer.text = new_answer.answer
        changed_answers.append(answer)

    session.add_all(changed_answers)

    return await get_templates_response(session=session,
                                        user_id=user_token.id)
