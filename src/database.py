from typing import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

def get_db(host, port, db_name, user, password) -> tuple[str, AsyncEngine, sessionmaker, Callable[[], AsyncGenerator[AsyncSession, None]]]:
    url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"
    engine = create_async_engine(url)
    session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            yield session
            await session.commit()

    return url, engine, session_maker, get_session

DATABASE_URL, engine, async_session_maker, get_async_session = get_db(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS)

Base = declarative_base()
