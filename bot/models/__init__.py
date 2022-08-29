from tortoise import Tortoise


async def setup(db_url: str, schemas: list[str]):
    await Tortoise.init(
        db_url=db_url,
        modules={
            'models': schemas
        }
    )
    await Tortoise.generate_schemas(safe=True)
