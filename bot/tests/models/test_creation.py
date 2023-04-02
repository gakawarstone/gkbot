from datetime import time

from tortoise import Tortoise

from settings import MODELS
from models import setup
from models.road import RoadSettings


async def test_models_initialisation():
    await setup('sqlite://:memory:', MODELS)
    await RoadSettings.create(
        user_id=123,
        focused_time=time(minute=15),
        relax_time=time(minute=15)
    )
