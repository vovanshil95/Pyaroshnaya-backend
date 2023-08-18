import pytest

from conftest import AsyncClient, user_in_db, authorisation

@pytest.mark.parametrize('username, status_code',
                         [('new_username', 200),
                          ('first_user', 409)])
async def test_change_username(ac: AsyncClient,
                               user_in_db,
                               authorisation,
                               username: str,
                               status_code: int):
    response = await ac.post('profile/changeUsername',
                             headers={'Authorization': authorisation,
                                      'user-agent': 'first-user-agent'},
                             json={'username': username})

    assert response.status_code == status_code

async def test_change_theme(ac: AsyncClient,
                            user_in_db,
                            authorisation):
    response = await ac.post('profile/changeTheme',
                             headers={'Authorization': authorisation,
                                      'user-agent': 'first-user-agent'},
                             json={'theme': 'DARK_THEME'})

    assert response.status_code == 200


async def test_get_profile(ac: AsyncClient,
                           user_in_db,
                           authorisation):
    response = await ac.get('profile/profile',
                            headers={'Authorization': authorisation,
                                     'user-agent': 'first-user-agent'})
    assert response.status_code == 200
    assert response.json()['data']['username'] == 'first_user'
    assert response.json()['data']['theme'] == 'LIGHT_THEME'