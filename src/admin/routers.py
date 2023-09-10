import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import aggregate_order_by

from auth.routes import get_admin_token
from database import get_async_session
from questions.schemas import AdminQuestion, AdminQuestionsResponse, FullOption, AdminCategoriesResponse, AdminCategory
from questions.schemas import Prompt as PromptSchema
from questions.models import Prompt as PromptModel, Answer
from questions.models import Question, Option, Category
from users.models import User

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

    session.add_all([Answer(id=uuid.uuid4(),
            question_id=question.id,
            user_id=user.id) for user in (await session.execute(select(User))).scalars().all()])

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

@router.post('/prompt', dependencies=[Depends(get_admin_token)])
async def change_add_prompt(prompt: PromptSchema,
                            session: AsyncSession=Depends(get_async_session)) -> AdminCategoriesResponse:

    await session.execute(delete(PromptModel).where(PromptModel.category_id == prompt.categoryId))
    await session.flush()

    session.add_all([PromptModel(id=uuid.uuid4(),
                                 category_id=prompt.categoryId,
                                 text=prompt_el,
                                 order_index=i) for i, prompt_el in enumerate(prompt.prompt)])
    await session.flush()

    categories = (await session.execute(
        select(Category, func.array_agg(aggregate_order_by(PromptModel.text, PromptModel.order_index)))
        .join(PromptModel, isouter=True)
        .group_by(Category.id)
        .order_by(Category.order_index)
    )).all()

    categories = [AdminCategory(id=category[0].id,
                                title=category[0].title,
                                description=category[0].description,
                                parentId=category[0].parent_id,
                                isMainScreenPresented=category[0].is_main_screen_presented,
                                isCategoryScreenPresented=category[0].is_category_screen_presented,
                                orderIndex=category[0].order_index,
                                prompt=category[1]) for category in categories]

    return AdminCategoriesResponse(message='status success', categories=categories)