

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from auth.routes import get_admin_token
from database import get_async_session
from questions.schemas import AdminQuestion, AdminQuestionsResponse, FullOption
from questions.models import Question, Option

router = APIRouter(prefix='/admin',
                   tags=['Admin'])

@router.post('/question', dependencies=[Depends(get_admin_token)])
async def change_add_question(question: AdminQuestion,
                              session: AsyncSession=Depends(get_async_session)) -> AdminQuestionsResponse:
    old_question = await session.get(Question, question.id)
    if old_question is not None:
        await session.delete(old_question)
        await session.flush()

    new_question = Question(id=question.id,
                            question_text=question.question,
                            is_required=question.isRequired,
                            category_id=question.categoryId,
                            order_index=question.orderIndex,
                            type_=question.questionType,
                            snippet=question.snippet)

    session.add(new_question)
    await session.flush()

    if question.questionType == 'options':
        options = [Option(id=option.id,
                          question_id=question.id,
                          option_text=option.text,
                          text_to_prompt=option.text_to_prompt) for option in question.options]
        session.add_all(options)

    questions = (await session.execute(select(Question,
                                              func.array_agg(Option.id),
                                              func.array_agg(Option.option_text),
                                              func.array_agg(Option.text_to_prompt))
                              .join(Option, isouter=True)
                              .where(Question.category_id == question.categoryId)
                              .group_by(Question.id)
                              .order_by(Question.order_index))).all()
    question_schemas = [AdminQuestion(id=question[0].id,
                                      question=question[0].question_text,
                                      snippet=question[0].snippet,
                                      isRequired=question[0].is_required,
                                      categoryId=question[0].category_id,
                                      questionType=question[0].type_,
                                      orderIndex=question[0].order_index,
                                      options=[FullOption(id=id,
                                                          text=text,
                                                          text_to_prompt=prompt_text)
                                               for id,text,prompt_text in zip(question[1], question[2], question[3])]
                                      if question[1] != [None] else None)
                        for question in questions]

    return AdminQuestionsResponse(message='status success', questions=question_schemas)