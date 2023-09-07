from tortoise import Tortoise

from models import setup


MODELS = [
    'models.users',
    'models.road',
    'models.books',
    'models.timezone',
    'models.tasks',
]


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
