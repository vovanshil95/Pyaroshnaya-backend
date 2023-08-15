import  pytest
from sqlalchemy import update

from conftest import AsyncClient, async_session_maker_test, categories_in_db, questions_in_db, authorisation
from questions.models import Question

async def test_get_categories(ac: AsyncClient,
                              categories_in_db):
    response = await ac.get('/question/categories')
    assert response.status_code == 200
    assert len(response.json()['categories']) == 2
    assert response.json()['categories'][0]['title']  == 'super-test-category-1'
    assert response.json()['categories'][1]['title']  == 'super-test-category-2'
    assert response.json()['categories'][0]['orderIndex']  == '0'
    assert response.json()['categories'][1]['orderIndex'] == '1'

async def test_get_questions(ac: AsyncClient,
                             questions_in_db,
                             authorisation):

    response = await ac.get('/question/questions',
                            headers={'Authorization': authorisation},
                            params={'categoryId': questions_in_db[0]})
    assert response.status_code == 200
    assert len(response.json()['questions']) == 3
    question_texts = set(map(lambda q: q['Question'], response.json()['questions']))
    assert question_texts == {'super-question-test-text-1', 'super-question-test-text-2', 'super-question-test-text-3'}
    first_question = list(filter(lambda q: q['Question'] == 'super-question-test-text-1',
                                 response.json()['questions']))[0]
    assert first_question['Answer'] == 'super-answer-1'

@pytest.mark.parametrize('all_answers_required, status_code',
                         [(False, 200),
                          (True, 400)])
async def test_gpt_response(ac: AsyncClient,
                            questions_in_db,
                            authorisation,
                            all_answers_required: bool,
                            status_code: int):

    if all_answers_required:
        async with async_session_maker_test.begin() as session:
            await session.execute(update(Question).values(is_required=True))

    response = await ac.post('/question/response',
                             headers={'Authorization': authorisation},
                             json={'categoryId': questions_in_db[0].hex})

    assert response.status_code == status_code
    if status_code == 200:
        assert len(response.json()) == 3
        question_texts = set(map(lambda q: q['Question'], response.json()))
        assert question_texts == {'super-question-test-text-1', 'super-question-test-text-2', 'super-question-test-text-3'}