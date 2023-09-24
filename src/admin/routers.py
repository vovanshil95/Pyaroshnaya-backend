import uuid
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.orm import aliased

from admin.schemas import ProductsResponse
from auth.routes import get_admin_token
from auth.utils import AccessTokenPayload
from database import get_async_session
from questions.routers import get_question_schemas, filled_prompt_generator, get_question_data
from questions.schemas import AdminQuestion, AdminQuestionsResponse, FullOption, AdminCategoriesResponse, AdminCategory, \
    UnfilledPromptResponse, PromptResponse
from questions.schemas import Prompt as PromptSchema
from questions.schemas import Category as CategorySchema
from questions.models import Prompt as PromptModel, Answer, Prompt
from questions.models import Question, Option
from questions.models import Category as CategoryModel
from users.models import User
from payment.schemas import Product as ProductSchema
from payment.schemas import PromoCode as PromoCodeSchema
from payment.models import ProductCategory
from payment.models import Product as ProductModel
from payment.models import PromoCode as PromoCodeModel

router = APIRouter(prefix='/admin',
                   tags=['Admin'])


async def get_admin_categories(session: AsyncSession):
    categories = (await session.execute(
        select(CategoryModel, func.array_agg(aggregate_order_by(PromptModel.text, PromptModel.order_index)))
        .join(PromptModel, isouter=True)
        .group_by(CategoryModel.id)
        .order_by(CategoryModel.order_index)
    )).all()

    categories = [AdminCategory(id=category[0].id,
                                title=category[0].title,
                                description=category[0].description,
                                parentId=category[0].parent_id,
                                isMainScreenPresented=category[0].is_main_screen_presented,
                                isCategoryScreenPresented=category[0].is_category_screen_presented,
                                orderIndex=category[0].order_index,
                                prompt=category[1] if category[1] != [None] else []) for category in categories]

    return AdminCategoriesResponse(message='status success', categories=categories)

async def get_admin_questions(session: AsyncSession,
                              category_id: uuid.UUID) -> AdminQuestionsResponse:
    questions = (await session.execute(select(Question,
                                              func.array_agg(Option.id),
                                              func.array_agg(Option.option_text),
                                              func.array_agg(Option.text_to_prompt))
                              .join(Option, isouter=True)
                              .where(Question.category_id == category_id)
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

async def get_products_(session: AsyncSession) -> ProductsResponse:

    categories = (await session.execute(select(ProductCategory)
                                        .order_by(ProductCategory.category_id))).scalars().all()
    promos = (await session.execute(select(PromoCodeModel)
                                    .order_by(PromoCodeModel.id))).scalars().all()
    products = (await session.execute(select(ProductModel)
                                      .where(ProductModel.active)
                                      .order_by(ProductModel.price_rubbles))).scalars().all()

    categories_dict = {category.category_id: [] for category in categories}
    promos_dict = {product.id: [] for product in products}
    for category in categories:
        categories_dict[category.product_id].append(category.category_id)
    for promo in promos:
        promos_dict[promo.product_id].append(PromoCodeSchema(
            id=promo.id,
            code=promo.code,
            discountAbsolute=promo.discount_absolute,
            discountPercent=promo.discount_percent
        ))

    products = [ProductSchema(
        id=product.id,
        title=product.title,
        priceRubbles=product.price_rubbles,
        availabilityDurationDays=product.availability_duration_days,
        usageCount=product.usage_count,
        description=product.description,
        returnUrl=product.return_url,
        promoCodes=promos_dict[product.id],
        categoryIds=categories_dict[product.id]
    ) for product in products]

    return ProductsResponse(message='status success',
                            data=products)


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

    session.add_all([Answer(id=uuid.uuid4(),
            question_id=question.id,
            user_id=user.id) for user in (await session.execute(select(User))).scalars().all()])

    return await get_admin_questions(session, question.categoryId)

@router.get('/prompt', dependencies=[Depends(get_admin_token)])
async def get_prompt(categoryId: uuid.UUID,
                     session: AsyncSession=Depends(get_async_session)) -> UnfilledPromptResponse:
    prompt = (await session.execute(select(PromptModel)
                                    .where(PromptModel.category_id == categoryId)
                                    .order_by(PromptModel.order_index))).scalars().all()
    return UnfilledPromptResponse(message='status success',
                                  prompt=[prompt_el.text for prompt_el in prompt])

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
    return await get_admin_categories(session)


@router.post('/category', dependencies=[Depends(get_admin_token)])
async def add_change_category(category: CategorySchema,
                              session: AsyncSession=Depends(get_async_session)) -> AdminCategoriesResponse:
    old_category = await session.get(CategoryModel, category.id)
    if old_category is None:
        session.add(CategoryModel(id=category.id,
                                  title=category.title,
                                  is_category_screen_presented=category.isCategoryScreenPresented,
                                  is_main_screen_presented=category.isCategoryScreenPresented,
                                  order_index=category.orderIndex,
                                  description=category.description,
                                  parent_id=category.parentId))
    else:
        old_category.order_index = category.orderIndex
        old_category.title = category.title
        old_category.is_category_screen_presented = category.isCategoryScreenPresented
        old_category.is_main_screen_presented = category.isMainScreenPresented
        old_category.description = category.description
        old_category.parent_id = category.parentId
        session.add(old_category)

    await session.flush()
    return await get_admin_categories(session)

@router.delete('/category', dependencies=[Depends(get_admin_token)])
async def delete_category(categoryId: uuid.UUID,
                          session: AsyncSession=Depends(get_async_session)) -> AdminCategoriesResponse:
    category = await session.get(CategoryModel, categoryId)
    await session.delete(category)
    await session.flush()
    return await get_admin_categories(session)

@router.delete('/question', dependencies=[Depends(get_admin_token)])
async def delete_question(questionId: uuid.UUID,
                          session: AsyncSession=Depends(get_async_session)) -> AdminQuestionsResponse:
    question = await session.get(Question, questionId)
    await session.delete(question)
    await session.flush()
    return await get_admin_questions(session, question.category_id)

@router.get('/questions', dependencies=[Depends(get_admin_token)])
async def get_questions(categoryId: uuid.UUID,
                        session: AsyncSession=Depends(get_async_session)) -> AdminQuestionsResponse:
    return await get_admin_questions(session, categoryId)

@router.get('/filledPrompt')
async def get_prompt(categoryId: uuid.UUID,
                     user_token: AccessTokenPayload=Depends(get_admin_token),
                     session: AsyncSession=Depends(get_async_session),
                     get_filled_prompt: Callable=Depends(filled_prompt_generator)) -> PromptResponse :
    questions_data = await get_question_data(user_token.id, session, categoryId)
    questions = get_question_schemas(questions_data)
    for question in questions:
        if question.isRequired and not question.answers and not question.answer:
            raise HTTPException(status_code=400, detail='required fields not filled')

    prompt = (await session.execute(select(Prompt.text)
                                    .where(Prompt.category_id == categoryId)
                                    .order_by(Prompt.order_index))).scalars().all()

    filled_prompt = await get_filled_prompt(questions, prompt, session)

    return PromptResponse(message='status success', questions=questions, filledPrompt=filled_prompt)

@router.post('/product', dependencies=[Depends(get_admin_token)])
async def add_change_product(product: ProductSchema,
                             session: AsyncSession=Depends(get_async_session)) -> ProductsResponse:
    product_model = await session.get(ProductModel, product.id)
    if product_model is not None:
        product_model.description = product.description
        product_model.return_url = product_model.return_url
        product_model.price_rubbles = product.priceRubbles
        product_model.availability_duration_days = product.availabilityDurationDays
        product_model.title = product.title
        product_model.usage_count = product.usageCount
        await session.execute(delete(PromoCodeModel).where(PromoCodeModel.product_id == product.id))
        await session.execute(delete(ProductCategory).where(ProductCategory.product_id == product.id))
    else:
        session.add(ProductModel(
            id=product.id,
            price_rubbles=product.priceRubbles,
            description=product.description,
            return_url=product.returnUrl,
            title=product.title,
            active=True,
            availability_duration_days=product.availabilityDurationDays,
            usage_count=product.usageCount
        ))
    await session.flush()
    session.add_all([ProductCategory(
        product_id=product.id,
        category_id=category_id
    ) for category_id in product.categoryIds])
    session.add_all([PromoCodeModel(
        id=promo_code.id,
        code=promo_code.code,
        product_id=product.id,
        discount_absolute=promo_code.discountAbsolute,
        discount_percent=promo_code.discountPercent
    ) for promo_code in product.promoCodes])

    return await get_products_(session=session)


@router.get('/product', dependencies=[Depends(get_admin_token)])
async def get_products(session: AsyncSession=Depends(get_async_session)) -> ProductsResponse:
    return await get_products_(session=session)

@router.delete('/product', dependencies=[Depends(get_admin_token)])
async def delete_product(productId: uuid.UUID,
                         session: AsyncSession=Depends(get_async_session)) -> ProductsResponse:
    product = await session.get(ProductModel, productId)
    product.active = False
    return await get_products_(session=session)
