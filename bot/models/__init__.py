from tortoise import Tortoise

from configs import db


async def setup(db_url: str | None = None, schemas: list[str] = db.MODELS):
    if db_url:
        await Tortoise.init(db_url=db_url, modules={"models": schemas})
    else:
        config = db.build_db_config_from_env(schemas)
        await Tortoise.init(config=config)

    await Tortoise.generate_schemas(safe=True)
