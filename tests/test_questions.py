import uuid

import  pytest
from sqlalchemy import delete, update

from conftest import AsyncClient, async_session_maker_test, user_in_db
from questions.models import Category, Question, Answer


@pytest.fixture()
async def categories_in_db():
    async with async_session_maker_test.begin() as session:
        first_id = uuid.uuid4()
        second_id = uuid.uuid4()
        session.add(Category(id=first_id,
                             title='super-test-category-1',
                             description='super-test-category-1-description',
                             parent_id=None))
        await session.flush()
        session.add(Category(id=second_id,
                             title='super-test-category-2',
                             description='super-test-category-2-description',
                             parent_id=first_id))
    yield first_id, second_id
    async with async_session_maker_test.begin() as session:
        await session.execute(delete(Category))

@pytest.fixture()
async def questions_in_db(categories_in_db, user_in_db):
    async with async_session_maker_test.begin() as session:
        first_question_id = uuid.uuid4()
        session.add(Question(id=first_question_id,
                             question_text='super-question-test-text-1',
                             is_required=True,
                             category_id=categories_in_db[0]))
        session.add(Question(id=uuid.uuid4(),
                             question_text='super-question-test-text-2',
                             is_required=False,
                             category_id=categories_in_db[0],
                             snippet='super-test-snippet-1'))
        session.add(Question(id=uuid.uuid4(),
                             question_text='super-question-test-text-3',
                             is_required=True,
                             category_id=categories_in_db[1]))
        await session.flush()
        session.add(Answer(id=uuid.uuid4(),
                           question_id=first_question_id,
                           text='super-answer-1',
                           user_id=user_in_db))
    yield categories_in_db
    async with async_session_maker_test.begin() as session:
        await session.execute(delete(Question))
        await session.execute(delete(Answer))


async def test_get_categories(ac: AsyncClient,
                              categories_in_db):
    response = await ac.get('/question/categories')
    assert response.status_code == 200
    assert len(response.json()['categories']) == 2
    assert response.json()['categories'][0]['title']  == 'super-test-category-1'
    assert response.json()['categories'][1]['title']  == 'super-test-category-2'

async def test_get_questions(ac: AsyncClient,
                             questions_in_db):
    login_response = await ac.post('/auth/login',
                                   headers={'user-agent': 'second-user-agent'},
                                   json={'username': 'first_user',
                                   'password': '1234'})
    authorisation = f"Bearer {login_response.json()['accessToken']}"

    response = await ac.get('/question/questions',
                            headers={'Authorization': authorisation},
                            params={'categoryId': questions_in_db[0]})
    assert response.status_code == 200
    assert len(response.json()['questions']) == 2
    question_texts = set(map(lambda q: q['Question'], response.json()['questions']))
    assert question_texts == {'super-question-test-text-1', 'super-question-test-text-2'}
    first_question = list(filter(lambda q: q['Question'] == 'super-question-test-text-1',
                                 response.json()['questions']))[0]
    assert first_question['Answer'] == 'super-answer-1'

@pytest.mark.parametrize('all_answers_required, status_code',
                         [(False, 200),
                          (True, 400)])
async def test_gpt_response(ac: AsyncClient,
                            questions_in_db,
                            all_answers_required: bool,
                            status_code: int):

    if all_answers_required:
        async with async_session_maker_test.begin() as session:
            await session.execute(update(Question).values(is_required=True))

    login_response = await ac.post('/auth/login',
                                   headers={'user-agent': 'second-user-agent'},
                                   json={'username': 'first_user',
                                   'password': '1234'})
    authorisation = f"Bearer {login_response.json()['accessToken']}"

    response = await ac.post('/question/response',
                             headers={'Authorization': authorisation},
                             json={'categoryId': questions_in_db[0].hex})

    assert response.status_code == status_code
    if status_code == 200:
        assert len(response.json()) == 2
        question_texts = set(map(lambda q: q['Question'], response.json()))
        assert question_texts == {'super-question-test-text-1', 'super-question-test-text-2'}