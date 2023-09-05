import uuid

import pytest

from conftest import AsyncClient, questions_in_db, authorisation


async def test_get_history(ac: AsyncClient,
                           questions_in_db,
                           authorisation):
    await ac.post('/question/response',
                  headers={'Authorization': authorisation},
                  json={'categoryId': questions_in_db[0][0].hex})

    response = await ac.get('/history/gptHistory',
                            params={'categoryId': questions_in_db[0][0].hex},
                            headers={'Authorization': authorisation})
    assert response.status_code == 200
    interactions = response.json()['data']
    assert len(interactions) == 1
    assert len(interactions[0]['questions']) == 2
    assert set(map(lambda el: el['answer'], interactions[0]['questions'])) == {'super-answer-1', 'super-answer-3'}

@pytest.mark.parametrize('change_id, status_code',
                        [(False, 200),
                         (True, 404)])
async def test_add_to_favorite(ac: AsyncClient,
                               questions_in_db,
                               authorisation,
                               change_id: bool,
                               status_code: int):
    await ac.post('/question/response',
                  headers={'Authorization': authorisation},
                  json={'categoryId': questions_in_db[0][0].hex})

    interaction_id = (await ac.get('/history/gptHistory',
                             headers={'Authorization': authorisation})).json()['data'][0]['id']

    if change_id:
        interaction_id = uuid.uuid4().hex

    response = await ac.post('/history/gptHistoryFavorite',
                             headers={'Authorization': authorisation},
                             json={'id': interaction_id})

    assert response.status_code == status_code
    if status_code == 200:
        print(response.json())
        exit(0)
        interactions = response.json()['data']
        assert len(interactions) == 1
        assert interactions[0]['isFavorite']

@pytest.mark.parametrize('change_id, status_code',
                        [(False, 200),
                         (True, 404)])
async def test_delete_from_favorite(ac: AsyncClient,
                                    questions_in_db,
                                    authorisation,
                                    change_id: bool,
                                    status_code: int):
    await ac.post('/question/response',
                  headers={'Authorization': authorisation},
                  json={'categoryId': questions_in_db[0][0].hex})

    interaction_id = (await ac.get('/history/gptHistory',
                             headers={'Authorization': authorisation})).json()['data'][0]['id']

    if change_id:
        interaction_id = uuid.uuid4().hex

    await ac.post('/history/gptHistoryFavorite',
                        headers={'Authorization': authorisation},
                        json={'id': interaction_id})
    response = await ac.delete('/history/gptHistoryFavorite',
                               headers={'Authorization': authorisation},
                               params={'id': interaction_id})

    assert response.status_code == status_code
    if status_code == 200:
        interactions = response.json()['data']
        assert len(interactions) == 1
        assert not interactions[0]['isFavorite']
