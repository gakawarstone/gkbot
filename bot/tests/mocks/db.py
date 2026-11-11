from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from tortoise import Tortoise

from configs.db import MODELS


def use_db(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        await Tortoise.init(db_url="sqlite://:memory:", modules={"models": MODELS})
        await Tortoise.generate_schemas(safe=True)

        try:
            result = await func(*args, **kwargs)
        finally:
            await Tortoise.close_connections()

        return result

    return wrapper
