from collections.abc import Awaitable, Callable
from functools import wraps
from unittest.mock import patch

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from configs import db
from models.base import Base


def use_db[**Parameters, Result](
    func: Callable[Parameters, Awaitable[Result]],
) -> Callable[Parameters, Awaitable[Result]]:
    @wraps(func)
    async def wrapper(*args: Parameters.args, **kwargs: Parameters.kwargs) -> Result:
        test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
        try:
            async with test_engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            with patch.object(db, "SessionLocal", test_session_factory):
                return await func(*args, **kwargs)
        finally:
            await test_engine.dispose()

    return wrapper
