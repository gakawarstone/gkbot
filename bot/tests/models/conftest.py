import pytest
from tortoise import Tortoise
from tortoise.contrib.test import finalizer, initializer

from settings import MODELS


async def setup(db_url: str, schemas: list[str]):
    await Tortoise.init(
        db_url=db_url,
        modules={
            'models': schemas
        }
    )
    await Tortoise.generate_schemas(safe=True)


@pytest.fixture(scope="session", autouse=True)
def initialize_models(request):
    request.addfinalizer(finalizer)
