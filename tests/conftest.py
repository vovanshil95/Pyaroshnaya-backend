import asyncio
import sys
from typing import AsyncGenerator

import pytest_asyncio as pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

sys.path.append(sys.path[0].replace('tests', 'src'))

from database import get_db, get_async_session
from config import TEST_DB_HOST, TEST_DB_PORT, TEST_DB_NAME, TEST_DB_USER, TEST_DB_PASS
from auth.models import Base
from main import app

_, test_engine, async_session_maker, test_get_async_session =  get_db(TEST_DB_HOST, TEST_DB_PORT, TEST_DB_NAME, TEST_DB_USER, TEST_DB_PASS)

Base.metadata.bind = test_engine

app.dependency_overrides[get_async_session] = test_get_async_session

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
