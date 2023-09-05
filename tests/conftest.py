import asyncio
import sys
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest_asyncio as pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(sys.path[0].replace('tests', 'src'))

from main import app
from database import get_db, get_async_session
from config import TEST_DB_HOST, TEST_DB_PORT, TEST_DB_NAME, TEST_DB_USER, TEST_DB_PASS
from auth.utils import encrypt
from users.models import User
from auth.models import Base, Auth, RefreshToken
from questions.models import Category, Answer, Prompt
from questions.models import Question as QuestionModel
from questions.routers import get_gpt_send, get_filled_prompt
from questions.schemas import Question as QuestionSchema

_, test_engine, async_session_maker_test, get_async_session_test =  get_db(TEST_DB_HOST, TEST_DB_PORT, TEST_DB_NAME, TEST_DB_USER, TEST_DB_PASS)

Base.metadata.bind = test_engine

def get_gpt_send_test():
    async def get_gpt_response(questions: list[QuestionSchema], prompt: list[str], session: AsyncSession) -> str:
        filled_prompt = await get_filled_prompt(questions, prompt, session)
        return f'test response not from gpt to prompt {filled_prompt}'

    return get_gpt_response

app.dependency_overrides[get_async_session] = get_async_session_test
app.dependency_overrides[get_gpt_send] = get_gpt_send_test

@pytest.fixture(autouse=True, scope='session')
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope='session')
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

client = TestClient(app)

@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture()
async def user_in_db():
    async with async_session_maker_test.begin() as session:
        user_id = uuid.uuid4()
        session.add(User(id=user_id,
                         name='first_user',
                         company='super_company',
                         role='user',
                         chat_id=1234))
        await session.flush()
        session.add(Auth(id=uuid.uuid4(),
                         user_id=user_id,
                         password=encrypt('1234')))
        session.add(RefreshToken(id=uuid.uuid4(),
                                 user_id=user_id,
                                 user_agent='first-user-agent',
                                 exp=datetime.utcnow() + timedelta(days=20),
                                 last_use=datetime.utcnow() - timedelta(minutes=10)))
    yield user_id
    async with async_session_maker_test.begin() as session:
        await session.execute(delete(RefreshToken))
        await session.execute(delete(Auth))
        await session.execute(delete(User))

@pytest.fixture()
async def authorisation(ac: AsyncClient):
    login_response = await ac.post('/auth/login',
                                   headers={'user-agent': 'second-user-agent'},
                                   json={'username': 'first_user',
                                   'password': '1234'})
    yield f"Bearer {login_response.json()['accessToken']}"
    async with async_session_maker_test.begin() as session:
        await session.execute(delete(RefreshToken))

@pytest.fixture()
async def categories_in_db():
    async with async_session_maker_test.begin() as session:
        first_id = uuid.uuid4()
        second_id = uuid.uuid4()
        session.add(Category(id=first_id,
                             title='super-test-category-1',
                             is_main_screen_presented=True,
                             is_category_screen_presented=False,
                             order_index='0',
                             description='super-test-category-1-description',
                             parent_id=None))
        await session.flush()
        session.add(Category(id=second_id,
                             title='super-test-category-2',
                             is_main_screen_presented=False,
                             is_category_screen_presented=True,
                             order_index='1',
                             description='super-test-category-2-description',
                             parent_id=first_id))
        await session.flush()
        session.add(Prompt(id=uuid.uuid4(),
                           category_id=first_id,
                           text='super prompt 1 {1}',
                           order_index=0))
        session.add(Prompt(id=uuid.uuid4(),
                           category_id=first_id,
                           text='super prompt 2 {2}',
                           order_index=1))
        session.add(Prompt(id=uuid.uuid4(),
                           category_id=second_id,
                           text='super prompt 3 {2}',
                           order_index=0))
        session.add(Prompt(id=uuid.uuid4(),
                           category_id=second_id,
                           text='super prompt 4 {1}',
                           order_index=1))
    yield first_id, second_id
    async with async_session_maker_test.begin() as session:
        await session.execute(delete(Category))

@pytest.fixture()
async def questions_in_db(categories_in_db, user_in_db):
    async with async_session_maker_test.begin() as session:
        first_question_id = uuid.uuid4()
        second_question_id = uuid.uuid4()
        third_question_id = uuid.uuid4()
        fourth_question_id = uuid.uuid4()
        session.add(QuestionModel(id=first_question_id,
                                  question_text='super-question-test-text-1',
                                  is_required=True,
                                  category_id=categories_in_db[0],
                                  order_index=0,
                                  type_='text'))
        session.add(QuestionModel(id=second_question_id,
                                  question_text='super-question-test-text-2',
                                  is_required=False,
                                  category_id=categories_in_db[0],
                                  snippet='super-test-snippet-2',
                                  order_index=1,
                                  type_='text'))
        session.add(QuestionModel(id=third_question_id,
                                  question_text='super-question-test-text-3',
                                  is_required=True,
                                  category_id=categories_in_db[0],
                                  snippet='super-test-snippet-3',
                                  order_index=2,
                                  type_='text'))
        session.add(QuestionModel(id=fourth_question_id,
                                  question_text='super-question-test-text-4',
                                  is_required=True,
                                  category_id=categories_in_db[1],
                                  order_index=0,
                                  type_='text'))
        await session.flush()
        session.add(Answer(id=uuid.uuid4(),
                           question_id=first_question_id,
                           text='super-answer-1',
                           user_id=user_in_db))
        session.add(Answer(id=uuid.uuid4(),
                           question_id=third_question_id,
                           text='super-answer-3',
                           user_id=user_in_db))
    yield categories_in_db, [first_question_id,
                             second_question_id,
                             third_question_id,
                             fourth_question_id]
    async with async_session_maker_test.begin() as session:
        await session.execute(delete(QuestionModel))
        await session.execute(delete(Answer))
