import uuid

import pytest
from sqlalchemy import update

from conftest import AsyncClient, user_in_db, async_session_maker_test, authorisation, questions_in_db
from questions.models import Answer
from templates.models import Template


@pytest.fixture()
async def templates_in_db(questions_in_db,
                          user_in_db):
    async with async_session_maker_test.begin() as session:
        template = Template(id=(template_id := uuid.uuid4()),
                            user_id=user_in_db,
                            title='super template')
        session.add(template)
        await session.flush()

        await session.execute(
            update(Answer)
            .where(Answer.question_id.in_(questions_in_db[1][:3]))
            .values(template_id=template_id)
        )
    yield
    async with async_session_maker_test.begin() as session:
        await session.delete(template)

async def test_get_templates(ac: AsyncClient,
                             templates_in_db,
                             authorisation):

    response = await ac.get('/templates',
                            headers={'Authorization': authorisation})
    assert response.status_code == 200
    temlates = response.json()['templates']
    assert len(temlates) == 1

async def test_add_template(ac: AsyncClient,
                            user_in_db,
                            questions_in_db,
                            authorisation):
    response = await ac.put('/templates',
                            headers={'Authorization': authorisation},
                            json={'categoryId': questions_in_db[0][0].hex,
                                  'title': 'super template 1'})

    assert response.status_code == 200
    templates = response.json()['templates']
    assert len(templates) == 1
    questions = templates[0]['questions']
    assert len(questions) == 4


async def test_change_templates(ac: AsyncClient,
                                user_in_db,
                                questions_in_db,
                                authorisation):
    templates_resp = await ac.put('/templates',
                                  headers={'Authorization': authorisation},
                                  json={'categoryId': questions_in_db[0][0].hex,
                                        'title': 'super template title 2'})

    template_id = templates_resp.json()['templates'][0]['id']
    questions = templates_resp.json()['templates'][0]['questions']
    question_ids = [questions[i]['id'] for i in range(len(questions))]

    response = await ac.post('/templates',
                             headers={'Authorization': authorisation},
                             json={'templateId': template_id,
                                   'title': 'super title',
                                   'newAnswers': [
                                       {'quetionId': question_id,
                                        'answer': f'super answer {i}'}
                                       for i,question_id in enumerate(question_ids)
                                   ]})

    assert response.status_code == 200
    questions = response.json()['templates'][0]['questions']
    answers = {question['answer'] for question in questions}
    assert {f'super answer {i}' for i in range(len(questions))} == answers


async def test_delete_template(ac: AsyncClient,
                               user_in_db,
                               questions_in_db,
                               authorisation):
    templates_resp = await ac.put('/templates',
                                  headers={'Authorization': authorisation},
                                  json={'categoryId': questions_in_db[0][0].hex,
                                        'title': 'super template title'})

    template_id = templates_resp.json()['templates'][0]['id']

    response = await ac.delete('/templates',
                               headers={'Authorization': authorisation},
                               params={'templateId': template_id})

    assert response.status_code == 200
    assert response.json()['templates'] == []
