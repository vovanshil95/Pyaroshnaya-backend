from datetime import datetime, timedelta

import  pytest
from sqlalchemy import update

from auth.models import RefreshToken
from conftest import async_session_maker_test, AsyncClient, user_in_db, authorisation

@pytest.mark.parametrize('name, password, user_agent, status_code',
                         [('first_user', '1234', 'second-user-agent', 200),
                          ('second_user', '1234', 'second-user-agent', 401),
                          ('first_user', '12345', 'second-user-agent', 401)])
async def test_login(ac: AsyncClient,
                     user_in_db,
                     name: str,
                     password: str,
                     status_code: int,
                     user_agent: str):
    response = await ac.post('/auth/login',
                             headers={'user-agent': user_agent},
                             json={'username': name,
                                   'password': password})
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

@pytest.mark.parametrize('old_password, status_code',
                         [('1234', 200),
                          ('12345', 409)])
async def test_change_password(ac: AsyncClient,
                               user_in_db,
                               authorisation,
                               old_password: str,
                               status_code: int):
    response = await ac.post('auth/changePassword',
                             headers={'Authorization': authorisation,
                                      'user-agent': 'first-user-agent'},
                             json={'oldPassword': old_password, 'newPassword': '12345'})

    assert response.status_code == status_code