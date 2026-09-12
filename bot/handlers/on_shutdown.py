from aiogram import Router
from tortoise import Tortoise

from services.schedule import Schedule


async def on_shutdown():
    await Schedule.on_shutdown()
    await Tortoise.close_connections()


def setup(r: Router):
    r.shutdown.register(on_shutdown)
