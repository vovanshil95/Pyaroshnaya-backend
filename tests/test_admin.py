import uuid

import pytest

from conftest import user_in_db, async_session_maker_test, AsyncClient
from users.models import User
from questions.schemas import AdminQuestion, FullOption


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


async def test_change_prompt(categories_in_db,
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