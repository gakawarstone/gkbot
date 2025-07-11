from tortoise import Tortoise

from . import env

MODELS = [
    "models.users",
    "models.road",
    "models.books",
    "models.timezone",
    "models.tasks",
]


async def on_startup():
    await Tortoise.init(db_url=env.DB_URL, modules={"models": MODELS})
    await Tortoise.generate_schemas(safe=True)
