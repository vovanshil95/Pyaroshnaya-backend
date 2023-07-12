from httpx import AsyncClient
import pytest

import uuid
import base64
import hmac

from config import SHA_KEY
from conftest import async_session_maker
from users.schemas import NewUser as NewUserSchema
from users.models import User
from auth.schemas import AccessTokenPayload
from auth.schemas import SmsVerification
from auth.models import Auth

@pytest.fixture()
async def user_schema_templates():
    return [NewUserSchema(username='vlad',
                         phone='+79115901599',
                         company='super_company',
                         password='123'),
            NewUserSchema(username='alex',
                          phone='+79115901598',
                          company='super_company',
                          password='123'),
            NewUserSchema(username='dmitriy',
                          phone='+79115901597',
                          company='super_company',
                          password='123')
            ]
@pytest.fixture(scope='module', autouse=True)
async def add_users_to_db(user_schema_templates):
    user_ids = [uuid.UUID(hex='469c6c65-73bc-4535-8767-243b31d6c397'),
                uuid.UUID(hex='cec34912-1474-4422-831c-9a83136bb4e7')]

    auth_ids = [uuid.UUID(hex='73cec3b5-911b-4540-b9a4-bc6a6f3cd306'),
                uuid.UUID(hex='73cec3b5-911b-4540-b9a4-bc6a6f3cd306')]

    async with async_session_maker.begin() as session:
        session.add_all(map(lambda user, id_template: User(id=id_template,
                                              name=user.name,
                                              phone=user.phone,
                                              company=user.company), user_schema_templates[1:], user_ids))

        await session.flush()
        session.add_all(map(lambda user_id, auth_id:
                            Auth(id=user_id,
                                 user_id=auth_id,
                                 pasword=hmac.new(SHA_KEY, user_schema_templates[1].password, 'sha256').digest()),
                            user_ids, auth_ids))
    yield


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

async def get_sms(success: str, ac: AsyncClient, resp, send_code_to):
    async with async_session_maker.begin() as session:
        sms_code = await session.get(Auth, uuid.UUID(hex=resp.json()['user_id'])).sms_code

    if not success:
        sms_code += 1

    method = ac.post if send_code_to == 'auth/smsCode' else ac.put

    response = await method(send_code_to,
                            json=SmsVerification(user_id=resp.json()['user_id'],
                            code=sms_code).json())
    return response

@pytest.fixture()
async def verification_phone_register_resp(register_resp, ac: AsyncClient, request):
    return get_sms(success=request.param['success'], ac=ac, resp=register_resp, send_code_to='auth/smsCode')

@pytest.fixture()
async def verification_phone_recovery_resp(password_recovery_get_sms_resp, ac: AsyncClient, request):
    return get_sms(success=request.param['success'],
                   ac=ac,
                   resp=password_recovery_get_sms_resp,
                   send_code_to='auth/passwordRecovery')

@pytest.fixture()
async def login_resp(request, user_schema_templates, ac: AsyncClient):
    if not request.param['success']:
        user_schema_templates[0].password += '1'
    return await ac.post('/auth/login',
                         json={'username': user_schema_templates[0].username,
                         'password': user_schema_templates[0].password},
                         headers=None if not request.param.get('with_headers') else
                         {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})

@pytest.fixture()
async def logout_resp(request, login_resp, ac: AsyncClient):
    token = login_resp.json()['accessToken']
    if request.param['invalid_token']:
        token += '1'
    return await ac.post('/auth/logout', headers=None
            if request.param['without_auth'] else {'Authorization': f'Bearer {token}'})

@pytest.fixture()
async def password_recovery_get_sms_resp(ac: AsyncClient, user_schema_templates, request):
    user = request.param['user']
    if request.param['change_phone']:
        user_schema_templates[user].phone += '1'
    return await ac.post(json={'phone': user_schema_templates[user].phone})

@pytest.fixture()
async def send_new_password_resp(ac: AsyncClient, password_recovery_get_sms_resp, user_schema_templates):
    response = await ac.put('/auth/newPassword', json={'user_id': user_schema_templates[2].id, 'password': '1234'})
    return response

@pytest.mark.run(order=0)
async def test_user_register_success(register_resp):
    assert register_resp.status_code == 200
    assert register_resp.json()['message'] == 'registration status success'

@pytest.mark.run(order=1)
async def test_user_register_success(register_resp):
    assert register_resp.status_code == 429
    assert register_resp.json()['message'] == 'Too many requests'

@pytest.mark.parametrize("verification_phone_register_resp", {'success': False}, indirect=True)
@pytest.mark.run(order=2)
async def test_sms_verification_fail(ac: AsyncClient, verification_phone_register_resp):
    assert verification_phone_register_resp.status_code == 421
    assert verification_phone_register_resp.json()['message'] == 'code is failed'

@pytest.mark.parametrize("verification_phone_register_resp", {'success': True}, indirect=True)
@pytest.mark.run(order=3)
async def test_sms_verification_success(ac: AsyncClient, verification_phone_register_resp, access_token_template):
    token_payload = base64.urlsafe_b64decode(verification_phone_register_resp.json()['accessToken'].split(b'.')[1].decode())
    assert verification_phone_register_resp.status_code == 200
    assert token_payload == access_token_template.json()

@pytest.mark.parametrize('login_resp', {'success': True, 'with_headers': False}, indirect=True)
async def test_user_login_success(login_resp):
    assert login_resp.status_code == 400
    assert login_resp.json()['message'] == 'error: User-Agent required'

@pytest.mark.parametrize('login_resp', {'success': True, 'with_headers': True}, indirect=True)
async def test_user_login_success(login_resp):
    assert login_resp.status_code == 200
    assert base64.urlsafe_b64decode(login_resp.json()['accessToken'].split(b'.')[1].decode()) == access_token_template.json()

@pytest.mark.parametrize('login_resp', {'success': False, 'with_headers': True}, indirect=True)
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
    assert register_resp.json()['message'] == 'User with same name already exists'

@pytest.mark.parametrize('register_resp', {'change_name': True}, indirect=True)
async def test_same_phone_user_register(ac: AsyncClient, register_resp):
    assert register_resp.status_code == 422
    assert register_resp.json()['message'] == 'User with same phone already exists'

@pytest.mark.parametrize('password_recovery_get_sms_resp',  {'change_phone': True, 'user': 0}, indirect=True)
async def test_password_recovery_get_sms_success(password_recovery_get_sms_resp):
    assert password_recovery_get_sms_resp.status_code == 200
    assert password_recovery_get_sms_resp.json()['message'] == 'status success: SMS-code was sent'

@pytest.mark.parametrize('password_recovery_get_sms_resp',  {'change_phone': False, 'user': 0}, indirect=True)
async def test_password_recovery_get_sms_second(password_recovery_get_sms_resp):
    assert password_recovery_get_sms_resp.status_code == 429
    assert password_recovery_get_sms_resp.json()['message'] == 'Too many requests'

@pytest.mark.parametrize('password_recovery_get_sms_resp',  {'change_phone': True, 'user': 0}, indirect=True)
async def test_password_recovery_get_sms_wrong_nuber():
    assert password_recovery_get_sms_resp.status_code == 421
    assert password_recovery_get_sms_resp.json()['message'] == 'The phone number was not found'


@pytest.mark.parametrize('verification_phone_recovery_resp', {'success': False}, indirect=True)
@pytest.mark.parametrize('password_recovery_get_sms_resp', {'user': 1}, indirect=True)
async def test_recovery_send_code_success(verification_phone_recovery_resp):
    assert verification_phone_recovery_resp.status_code == 421
    assert verification_phone_recovery_resp.json()['message'] == 'code is failed'

@pytest.mark.parametrize('verification_phone_recovery_resp', {'success': True}, indirect=True)
@pytest.mark.parametrize('password_recovery_get_sms_resp', {'user': 1}, indirect=True)
async def test_recovery_send_code_success(verification_phone_recovery_resp):
    assert verification_phone_recovery_resp.status_code == 200
    assert verification_phone_recovery_resp.json()['message'] == 'status success, phone verified'

@pytest.mark.parametrize('verification_phone_recovery_resp', {'success': True}, indirect=True)
@pytest.mark.parametrize('password_recovery_get_sms_resp', {'user': 2}, indirect=True)
async def test_new_password(send_new_password_resp):
    assert send_new_password_resp.status_code == 200
    assert send_new_password_resp.json()['message'] == 'status success, password was changed'
