import asyncio
import uuid
import random
import string
from datetime import timedelta, datetime

from sqlalchemy import select, update, delete

import bot.config_ as CONSTS
from auth.models import Auth, RefreshToken
from auth.utils import encrypt, generate_salted_password
from database import async_session_maker
from payment.models import Purchase, Product
from users.models import User
from questions.models import Question, Answer

loop = asyncio.new_event_loop()

async def add_user(chat_id: int):
    async with async_session_maker.begin() as session:
        password = ''.join(random.choices(string.hexdigits, k=4))
        if (user := (await session.execute(select(User).where(User.chat_id == chat_id))).scalar()) is None:
            names = (await session.execute(select(User.name))).all()
            while True:
                name = ''.join(random.choices(string.ascii_lowercase, k=4))
                if name not in names: break
            session.add(User(id=(user_id := uuid.uuid4()),
                             chat_id=chat_id,
                             name=name))
            await session.flush()

            encrypted_password, salt = generate_salted_password(password)

            session.add(Auth(id=uuid.uuid4(),
                             user_id=user_id,
                             password=encrypted_password,
                             salt=salt))

            questions = (await session.execute(select(Question))).scalars().all()
            session.add_all([Answer(id=uuid.uuid4(),
                                    question_id=question.id,
                                    user_id=user_id,
                                    text=None,
                                    interaction_id=None) for question in questions])

            product = (await session.execute(select(Product).where(Product.title == 'free'))).scalars().first()

            session.add(Purchase(
                id=uuid.uuid4(),
                user_id=user_id,
                product_id=product.id,
                expiration_time=datetime.now() + timedelta(days=product.availability_duration_days)
                if product.availability_duration_days is not None else None,
                remaining_uses=product.usage_count
            ))

        else:

            encrypted_password, salt = generate_salted_password(password)

            name = user.name
            await session.execute(update(Auth).where(Auth.user_id == user.id).values(password=encrypted_password, salt=salt,))
            await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))

    return name, password



def get_login_password(chat_id: int):
    name, password = loop.run_until_complete(add_user(chat_id))

    result = dict(login=name, password=password)
    return CONSTS.YOUR_LOGIN + result.get("login") + '\n' + CONSTS.YOUR_PASSWORD + result.get("password")
