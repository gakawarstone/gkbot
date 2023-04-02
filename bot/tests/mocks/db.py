from tortoise import Tortoise

from settings import MODELS
from models import setup


def use_db(func):
    async def wrapper(*args, **kwargs):
        await setup('sqlite://:memory:', MODELS)

        try:
            result = await func(*args, **kwargs)
        except Exception as e:
            await Tortoise.close_connections()
            raise e

        await Tortoise.close_connections()

        return result

    return wrapper
