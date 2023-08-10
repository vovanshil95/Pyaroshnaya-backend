import asyncio
import sys
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest_asyncio as pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import delete

sys.path.append(sys.path[0].replace('tests', 'src'))

from main import app
from database import get_db, get_async_session
from config import TEST_DB_HOST, TEST_DB_PORT, TEST_DB_NAME, TEST_DB_USER, TEST_DB_PASS
from auth.models import Base, Auth, RefreshToken
from auth.utils import encrypt
from users.models import User

_, test_engine, async_session_maker_test, get_async_session_test =  get_db(TEST_DB_HOST, TEST_DB_PORT, TEST_DB_NAME, TEST_DB_USER, TEST_DB_PASS)

Base.metadata.bind = test_engine

app.dependency_overrides[get_async_session] = get_async_session_test

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
                         phone='79123456',
                         company='super_company',
                         role='user',
                         status='verified',
                         balance=False))
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