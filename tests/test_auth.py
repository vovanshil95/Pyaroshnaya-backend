from httpx import AsyncClient
import pytest

import uuid
import base64

from auth.models import Auth
from conftest import async_session_maker
from users.schemas import NewUser as NewUserSchema
from auth.schemas import AccessTokenPayload
from auth.schemas import SmsVerification

@pytest.fixture()
async def user_schema_templates():
    return [NewUserSchema(username='vlad',
                         phone='+79115901599',
                         company='hello_company',
                         password='123'),
            NewUserSchema(username='alex',
                          phone='+79115901598',
                          company='hello_company',
                          password='123')
            ]

@pytest.fixture()
async def access_token_template(user_schema_templates):
    return AccessTokenPayload(id='736b8f84-5c08-4b42-ae42-4cab17c8570e',
                              username=user_schema_templates[0].user_name,
                              phone=user_schema_templates[0].phone,
                              role='user',
                              balance=0,
                              tillDate=0)


@pytest.fixture()
async def register_resp(ac: AsyncClient, user_schema_templates, request):
    if request.param.get('change_name'):
        user_schema_templates[0].username += '1'
    if request.param.get('change_phone'):
        user_schema_templates[0].phone += '1'
    response = await ac.post('/auth/registration', json=user_schema_templates[0].json())
    return response

@pytest.fixture()
async def sms_verification_resp(register_resp, ac: AsyncClient, request):
    async with async_session_maker.begin() as session:
        sms_code = await session.get(Auth, uuid.UUID(hex=register_resp.json()['user_id'])).sms_code

    if not request.param['success']:
        sms_code += 1

    response = await ac.post('/auth/smsCode', json=SmsVerification(user_id='vlad3',
                                                                   code=sms_code).json())
    return response

@pytest.fixture()
async def login_resp(request, user_schema_templates, ac: AsyncClient):
    if not request.param['success']:
        user_schema_templates[0].password += '1'
    return await ac.post('/auth/login',
                         json={'username': user_schema_templates[0].username,
                         'password': user_schema_templates[0].password})

@pytest.fixture()
async def logout_resp(request, login_resp, ac: AsyncClient):
    token = login_resp.json()['accessToken']
    if request.param['invalid_token']:
        token += '1'
    return await ac.post('/auth/logout', headers=None
            if request.param['without_auth'] else {'Authorization': f'Bearer {token}'})

@pytest.fixture()
async def password_recovery_get_sms_resp(ac: AsyncClient, user_schema_templates, request):
    if request.param['change_phone']:
        user_schema_templates[0].phone += '1'
    return await ac.post(json={'phone': user_schema_templates[0].phone})

@pytest.mark.run(order=0)
async def test_user_register_success(register_resp):
    assert register_resp.status_code == 200
    assert register_resp.json()['message'] == 'registration status success'

@pytest.mark.run(order=1)
async def test_user_register_success(register_resp):
    assert register_resp.status_code == 429
    assert register_resp.json()['message'] == 'Too many requests'

@pytest.mark.parametrize("sms_verification_resp", {'success': False}, indirect=True)
@pytest.mark.run(order=2)
async def test_sms_verification_fail(ac: AsyncClient, sms_verification_resp):
    assert sms_verification_resp.status_code == 421
    assert sms_verification_resp.json()['message'] == 'code is failed'

@pytest.mark.parametrize("sms_verification_resp", {'success': True}, indirect=True)
@pytest.mark.run(order=3)
async def test_sms_verification_success(ac: AsyncClient, sms_verification_resp, access_token_template):
    token_payload = base64.urlsafe_b64decode(sms_verification_resp.json()['accessToken'].split(b'.')[1].decode())
    assert sms_verification_resp.status_code == 200
    assert token_payload == access_token_template.json()

@pytest.mark.parametrize("login_resp", {'success': True}, indirect=True)
async def test_user_login_success(login_resp):
    assert login_resp.status_code == 200
    assert base64.urlsafe_b64decode(login_resp.json()['accessToken'].split(b'.')[1].decode()) == access_token_template.json()

@pytest.mark.parametrize("login_resp", {'success': False}, indirect=True)
async def test_user_login_fail(login_resp):
    assert login_resp.status_code == 401
    assert login_resp.json()['message'] == 'incorrect username and password'

@pytest.mark.parametrize('logout_resp', {'invalid_token': False, 'without_auth': False}, indirect=True)
async def test_user_logout_success(logout_resp):
    assert logout_resp.status_code == 200
    assert logout_resp.json()['message'] == 'status success, user logged out'

@pytest.mark.parametrize('logout_resp', {'invalid_token': True, 'without_auth': False}, indirect=True)
async def test_user_logout_invalid_token(logout_resp):
    assert logout_resp.status_code == 498
    assert logout_resp.json()['message'] == 'The access token is invalid'

@pytest.mark.parametrize('logout_resp', {'invalid_token': False, 'without_auth': True}, indirect=True)
async def test_user_logout_without_auth(logout_resp):
    assert logout_resp.status_code == 401
    assert logout_resp.json()['message'] == 'User is not authorized'

@pytest.mark.parametrize('register_resp', {'change_phone': True}, indirect=True)
async def test_same_name_user_register(register_resp):
    assert register_resp.status_code == 421
    assert register_resp.json()['message'] == 'user with same name already exists'

@pytest.mark.parametrize('register_resp', {'change_name': True}, indirect=True)
async def test_same_phone_user_register(ac: AsyncClient, register_resp):
    assert register_resp.status_code == 422
    assert register_resp.json()['message'] == 'user with same phone already exists'

@pytest.mark.parametrize('password_recovery_get_sms_resp',  {'change_phone': True}, indirect=True)
async def test_password_recovery_get_sms_success(password_recovery_get_sms_resp):
    assert password_recovery_get_sms_resp.status_code == 200
    assert password_recovery_get_sms_resp.json()['message'] == 'status success: SMS-code was sent'

@pytest.mark.parametrize('password_recovery_get_sms_resp',  {'change_phone': False}, indirect=True)
async def test_password_recovery_get_sms_second(password_recovery_get_sms_resp):
    assert password_recovery_get_sms_resp.status_code == 429
    assert password_recovery_get_sms_resp.json()['message'] == 'Too many requests'

@pytest.mark.parametrize('password_recovery_get_sms_resp',  {'change_phone': True}, indirect=True)
async def test_password_recovery_get_sms_wrong_nuber():
    assert password_recovery_get_sms_resp.status_code == 421
    assert password_recovery_get_sms_resp.json()['message'] == 'The phone number was not found'

