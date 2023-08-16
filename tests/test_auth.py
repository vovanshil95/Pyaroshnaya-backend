from datetime import datetime, timedelta
import uuid

import  pytest
from sqlalchemy import delete, update

from auth.models import Auth, RefreshToken, SmsSend
from auth.utils import encrypt
from users.models import User
from conftest import async_session_maker_test, AsyncClient, user_in_db, authorisation
from config import TEST_SMS_CODE

@pytest.fixture()
async def unverified_user_in_db():
    async with async_session_maker_test.begin() as session:
        user_id = uuid.uuid4()
        session.add(User(id=user_id,
                         name='second_user',
                         phone='791234567',
                         company='super_company',
                         role='user',
                         status='unverified',
                         balance=False))
        await session.flush()
        session.add(Auth(id=uuid.uuid4(),
                         user_id=user_id,
                         password=encrypt('1234'),
                         sms_code=TEST_SMS_CODE))
        session.add(SmsSend(ip='127.0.0.1',
                            user_agent='second-user-agent',
                            user_id=user_id,
                            time_send=datetime.utcnow()))
    yield
    async with async_session_maker_test.begin() as session:
        await session.execute(delete(RefreshToken))
        await session.execute(delete(Auth))
        await session.execute(delete(User))

@pytest.fixture()
async def sms_sent_to_user(user_in_db):
    async with async_session_maker_test.begin() as session:
        await session.execute(update(Auth).where(Auth.user_id == user_in_db).values(sms_code=TEST_SMS_CODE))
        session.add(SmsSend(ip='127.0.0.1',
                            user_id=user_in_db,
                            user_agent='second-user-agent',
                            time_send=datetime.utcnow()))
    yield
    async with async_session_maker_test.begin() as session:
        await session.execute(delete(SmsSend))


@pytest.mark.parametrize('name, status_code, phone', [('second_user', 200, '791234567'),
                                                     (None, 200, '791234567'),
                                                      ('second_user', 422, None),
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
         (None, '79123456', '1234', 'first-user-agent', 200)])
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

@pytest.mark.parametrize('phone, sms_code, user_agent, status_code',
                         [('791234567', TEST_SMS_CODE, 'second-user-agent', 200),
                          ('791234567', TEST_SMS_CODE + '1', 'second-user-agent', 421),
                          ('791234567', TEST_SMS_CODE, 'third-user-agent', 404),
                          ('7912345', TEST_SMS_CODE, 'second-user-agent', 404)])
async def test_sms_code(ac: AsyncClient,
                        unverified_user_in_db,
                        phone: str,
                        sms_code: str,
                        status_code: int,
                        user_agent: str):
    response = await ac.post('/auth/smsCode',
                             headers={'user-agent': user_agent},
                             json={'phone': phone,
                                   'code': sms_code})
    assert response.status_code == status_code

@pytest.mark.parametrize('with_token, chane_token, status_code',
                         [(True, False, 200),
                          (True, True, 498),
                          (False, False, 422)])
async def test_logout(ac: AsyncClient,
                      user_in_db,
                      authorisation,
                      with_token: bool,
                      chane_token: bool,
                      status_code: int):

    if chane_token:
        authorisation = authorisation[:-1]

    headers = {'user-agent': 'second-user-agent'}
    if with_token:
        headers['Authorization'] = authorisation

    response = await ac.post('/auth/logout',
                             headers=headers)

    assert response.status_code == status_code

@pytest.mark.parametrize('phone, second_request, status_code',
                         [('79123456', False, 200),
                          ('791234567', False, 421),
                          ('79123456', True, 429)])
async def test_get_phone(ac: AsyncClient,
                         user_in_db,
                         phone: str,
                         second_request: bool,
                         status_code: int):
    response = await ac.post('auth/passwordRecovery',
                             headers={'user-agent': 'second-user-agent'},
                             json={'phone': phone})
    if second_request:
        response = await ac.post('auth/passwordRecovery',
                                 headers={'user-agent': 'second-user-agent'},
                                 json={'phone': phone})
    assert response.status_code == status_code

@pytest.mark.parametrize('phone, sms_code, second_request, status_code',
                         [('79123456', TEST_SMS_CODE, False, 200),
                          ('79123456', TEST_SMS_CODE + '1', False, 421),
                          ('791234567', TEST_SMS_CODE, False, 404),
                          ('79123456', TEST_SMS_CODE, True, 421)])
async def test_code_verification_recovery(ac: AsyncClient,
                                          sms_sent_to_user,
                                          phone: str,
                                          sms_code: str,
                                          second_request: bool,
                                          status_code: int):
    response = await ac.put('/auth/passwordRecovery',
                            json={'phone': phone,
                                  'code': sms_code})
    if second_request:
        response = await ac.put('/auth/passwordRecovery',
                                json={'phone': phone,
                                      'code': sms_code})
    assert response.status_code == status_code

@pytest.mark.parametrize('change_token, second_request, status_code',
                         [(False, False, 200),
                          (True, False, 498),
                          (False, True, 498)])
async def test_get_new_password(ac: AsyncClient,
                                sms_sent_to_user,
                                change_token: bool,
                                second_request: bool,
                                status_code: int):
    verification_response = await ac.put('/auth/passwordRecovery',
                            json={'phone': '79123456',
                                  'code': TEST_SMS_CODE})
    token = verification_response.json()['token']

    if change_token:
        token = token[:-1]

    response = await ac.post('/auth/newPassword',
                             json={'token': token,
                                   'password': 'super-new-password'})

    if second_request:
        response = await ac.post('/auth/newPassword',
                                 json={'token': token,
                                       'password': 'super-new-password'})

    assert response.status_code == status_code

@pytest.mark.parametrize('user_agent, change_token, second_request, status_code',
                         [('second-user-agent', False, False, 200),
                          ('third-user-agent', False, False, 404),
                          ('second-user-agent', True, False, 498),
                          ('second-user-agent', False, True, 401)])
async def test_give_new_tokens(ac: AsyncClient,
                               user_in_db,
                               user_agent: str,
                               change_token: bool,
                               second_request: bool,
                               status_code: int):
    login_response = await ac.post('/auth/login',
                                   headers={'user-agent': 'second-user-agent'},
                                   json={'username': 'first_user',
                                   'password': '1234'})

    refresh_token = login_response.json()['refreshToken']

    if change_token:
        refresh_token = refresh_token[:-1]

    response = await ac.get('/auth/newTokens',
                            headers={'user-agent': user_agent,
                                     'Authorization': f'Bearer {refresh_token}'})
    if second_request:
        response = await ac.get('/auth/newTokens',
                                headers={'user-agent': user_agent,
                                         'Authorization': f'Bearer {refresh_token}'})

    assert response.status_code == status_code


@pytest.mark.parametrize('user_agent, change_token, second_request, expired_token, status_code',
                         [('second-user-agent', False, False, False, 200),
                          ('third-user-agent', False, False, False, 404),
                          ('second-user-agent', True, False, False, 498),
                          ('second-user-agent', False, True, False, 200),
                          ('second-user-agent', False, False, True, 403)])
async def test_get_new_access_token(ac: AsyncClient,
                                    user_in_db,
                                    user_agent: str,
                                    change_token: bool,
                                    second_request: bool,
                                    expired_token: bool,
                                    status_code: int):

    login_response = await ac.post('/auth/login',
                                   headers={'user-agent': 'second-user-agent'},
                                   json={'username': 'first_user',
                                   'password': '1234'})

    if expired_token:
        async with async_session_maker_test.begin() as session:
            await session.execute(update(RefreshToken)
                                  .where(RefreshToken.user_id == user_in_db)
                                  .values(exp=datetime.utcnow() - timedelta(days=1)))

    refresh_token = login_response.json()['refreshToken']

    if change_token:
        refresh_token = refresh_token[:-1]

    response = await ac.get('/auth/newAccessToken',
                            headers={'user-agent': user_agent,
                                     'Authorization': f'Bearer {refresh_token}'})
    if second_request:
        response = await ac.get('/auth/newTokens',
                                headers={'user-agent': user_agent,
                                         'Authorization': f'Bearer {refresh_token}'})

    assert response.status_code == status_code
