from datetime import datetime, timedelta
import uuid

import  pytest
from sqlalchemy import delete

from auth.models import Auth, RefreshToken
from auth.utils import encrypt
from users.models import User, UnverifiedUser
from conftest import async_session_maker_test, AsyncClient
from config import TEST_SMS_CODE

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
    yield
    async with async_session_maker_test.begin() as session:
        await session.execute(delete(RefreshToken))
        await session.execute(delete(Auth))
        await session.execute(delete(User))

@pytest.fixture()
async def unverified_user_in_db():
    async with async_session_maker_test.begin() as session:
        session.add(UnverifiedUser(id=uuid.uuid4(),
                                   user_name='second_user',
                                   phone='791234567',
                                   company='super_company',
                                   password=encrypt('1234')))
        session.add(Auth)
    yield
    async with async_session_maker_test.begin() as session:
        pass



@pytest.mark.parametrize('name, status_code, phone', [('second_user', 200, '791234567'),
                                                     (None, 200, '791234567'),
                                                     ('first_user', 409, '791234567'),
                                                     ('second_user', 409, '79123456')])
async def test_register(ac: AsyncClient, user_in_db, name: str, status_code: int, phone: str):
    response = await ac.post('/auth/registration',
                             headers={'user-agent': 'super-user-agent'},
                             json={'username': name,
                                   'phone': phone,
                                   'company': 'super_company',
                                   'password': '1234'})
    assert response.status_code == status_code

@pytest.mark.parametrize('name, phone, password, user_agent, status_code',
        [('first_user', None, '1234', 'second-user-agent', 200),
         (None, '79123456', '1234', 'second-user-agent', 200),
         ('first_user', '79123456', 'second-user-agent', '1234', 422),
         ('second_user', None, '1234', 'second-user-agent', 401),
         ('first_user', None, '12345', 'second-user-agent', 401),
         ((None, '79123456', '1234', 'first-user-agent', 409))])
async def test_login(ac: AsyncClient,
                     user_in_db,
                     name: str,
                     phone: str,
                     password: str,
                     status_code: int,
                     user_agent: str):
    response = await ac.post('/auth/login',
                             headers={'user-agent': user_agent},
                             json={'username': name,
                                   'phone': phone,
                                   'password': password})
    assert response.status_code == status_code


async def test_sms_code(ac: AsyncClient, ):
    ac.post()
