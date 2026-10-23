from tortoise import Tortoise

from configs.db import MODELS


def use_db(func):
    async def wrapper(*args, **kwargs):
        await Tortoise.init(db_url="sqlite://:memory:", modules={"models": MODELS})
        await Tortoise.generate_schemas(safe=True)

        try:
            result = await func(*args, **kwargs)
        finally:
            await Tortoise.close_connections()

        return result

    return wrapper
