import uuid

import pytest

from conftest import user_in_db, async_session_maker_test, AsyncClient
from users.models import User
from questions.schemas import AdminQuestion, FullOption, Category


def uuids_to_hex(dict_: dict):
    for key, value in dict_.items():
        if isinstance(value, uuid.UUID):
            dict_[key] = value.hex
        elif isinstance(value, dict):
            dict_[key] = uuids_to_hex(dict_[key])
        elif isinstance(value, list):
            dict_[key] = [uuids_to_hex(el) for el in value]
    return dict_


@pytest.fixture()
async def admin_in_db(user_in_db):
    async with async_session_maker_test.begin() as session:
        user = await session.get(User, user_in_db)
        user.role = 'admin'
        session.add(user)
    yield user

@pytest.mark.parametrize('new_question, questions_size',
                         [(True, 4),
                          (False, 3)])
async def test_change_questions(admin_in_db,
                                questions_in_db,
                                authorisation,
                                ac: AsyncClient,
                                new_question: bool,
                                questions_size: int):

    question = AdminQuestion(id=uuid.uuid4() if new_question else questions_in_db[1][2],
                             question='super question 1',
                             snippet='super snippet 1',
                             options=[FullOption(id=uuid.uuid4(),
                                                 text='super option text 1',
                                                 text_to_prompt='super text to prompt 1'),
                                      FullOption(id=uuid.uuid4(),
                                                 text='super option text 2',
                                                 text_to_prompt='super text to prompt 1')],
                             isRequired=True,
                             categoryId=questions_in_db[0][0],
                             questionType='options',
                             orderIndex=questions_size - 1).dict()

    question = uuids_to_hex(question)

    response = await ac.post('/admin/question',
                             headers={'Authorization': authorisation},
                             json=question)

    assert response.status_code == 200
    questions = response.json()['questions']
    assert len(questions) == questions_size
    assert questions[-1]['question'] == 'super question 1'
    assert questions[-1]['options'][0]['text'] == 'super option text 1'


async def test_add_change_prompt(categories_in_db,
                                 admin_in_db,
                                 authorisation,
                                 ac: AsyncClient):
    prompt = ['It is test prompt and here is first answer {1}',
              'It is second prompt and here is seconde answer {2}']

    response = await ac.post('/admin/prompt',
                             headers={'Authorization': authorisation},
                             json={'categoryId': categories_in_db[0].hex,
                                   'prompt': prompt})
    assert response.status_code == 200
    category = [category for category in response.json()['categories'] if uuid.UUID(hex=category['id']) == categories_in_db[0]][0]
    assert category['prompt'] == prompt

@pytest.mark.parametrize('new_category, categories_size',
                         ([True, 3],
                         [False, 2]))
async def test_add_change_category(admin_in_db,
                                   authorisation,
                                   questions_in_db,
                                   ac: AsyncClient,
                                   new_category: bool,
                                   categories_size: int):
    category = Category(id=uuid.uuid4() if new_category else questions_in_db[0][0],
                        title='super admin category title 1',
                        description='super admin category 1 description',
                        parent_id=None,
                        isMainScreenPresented=True,
                        isCategoryScreenPresented=True,
                        orderIndex='2').dict()

    category = uuids_to_hex(category)

    response = await ac.post('/admin/category',
                             headers={'Authorization': authorisation},
                             json=category)
    assert response.status_code == 200
    categories = response.json()['categories']
    assert len(categories) == categories_size
    categories[-1].pop('id')
    categories[-1].pop('prompt')
    category.pop('id')
    assert categories[-1] == category

async def test_delete_category(questions_in_db,
                               admin_in_db,
                               authorisation,
                               ac: AsyncClient):
    response = await ac.delete('/admin/category',
                               headers={'Authorization': authorisation},
                               params={'categoryId': questions_in_db[0][0]})

    assert response.status_code == 200
    categories = response.json()['categories']
    assert len(categories) == 1
    assert uuid.UUID(hex=categories[0]['id']) != questions_in_db[0][0]

async def test_get_unfilled_prompt(questions_in_db,
                                   admin_in_db,
                                   authorisation,
                                   ac: AsyncClient):

    response = await ac.get('/admin/prompt',
                            headers={'Authorization': authorisation},
                            params={'categoryId': questions_in_db[0][0]})

    assert response.status_code == 200
    assert response.json()['prompt'] == ['super prompt 1 {1}', 'super prompt 2 {2}']

async def test_delete_question(questions_in_db,
                               admin_in_db,
                               authorisation,
                               ac: AsyncClient):

    response = await ac.delete('/admin/question',
                               headers={'Authorization': authorisation},
                               params={'questionId': questions_in_db[1][0]})

    assert response.status_code == 200
    questions = response.json()['questions']
    assert len(questions) == 2
    assert questions_in_db[1][0] not in [uuid.UUID(hex=question['id']) for question in questions]


async def test_get_admin_questions(questions_in_db,
                                   admin_in_db,
                                   authorisation,
                                   ac: AsyncClient):
    response = await ac.get('/admin/questions',
                            headers={'Authorization': authorisation},
                            params={'categoryId': questions_in_db[0][0]})

    expected_question = AdminQuestion(id=uuid.uuid4(),
                                      question='super-question-test-text-1',
                                      isRequired=True,
                                      options=None,
                                      categoryId=questions_in_db[0][0],
                                      snippet=None,
                                      orderIndex=0,
                                      questionType='text').dict()
    expected_question.pop('id')
    expected_question.pop('categoryId')

    assert response.status_code == 200
    questions = response.json()['questions']
    assert len(questions) == 3
    first_question = questions[0]
    first_question.pop('id')
    first_question.pop('categoryId')
    assert first_question == expected_question
