from tortoise import Tortoise, run_async

from settings import MODELS, DB_URL


def setup():
    run_async(_setup())


async def _setup():
    await Tortoise.init(
        db_url=DB_URL,
        modules={
            'models': MODELS
        }
    )
    await Tortoise.generate_schemas(safe=True)
