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
                             user_id=user_in_db)
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
    assert temlates[0]['']