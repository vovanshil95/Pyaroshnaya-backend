import asyncio
import uuid
import random
import string

from sqlalchemy import select, update, delete

import bot.config_ as CONSTS
from auth.models import Auth, RefreshToken
from auth.utils import encrypt
from database import async_session_maker
from users.models import User

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
            session.add(Auth(id=uuid.uuid4(),
                             user_id=user_id,
                             password=encrypt(password)))
        else:
            name = user.name
            await session.execute(update(Auth).where(Auth.user_id == user.id).values(password=encrypt(password)))
            await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))

    return name, password



def get_login_password(chat_id: int):
    name, password = loop.run_until_complete(add_user(chat_id))

    result = dict(login=name, password=password)
    return CONSTS.YOUR_LOGIN + result.get("login") + '\n' + CONSTS.YOUR_PASSWORD + result.get("password")
