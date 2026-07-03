from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


class Base(DeclarativeBase):
    pass


async_engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=False,
)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)


async def get_db():
    async with async_session_factory() as session:
        yield session