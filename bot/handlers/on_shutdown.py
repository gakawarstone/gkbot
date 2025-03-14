from aiogram import Router
from tortoise import Tortoise


async def on_shutdown():
    await Tortoise.close_connections()


def setup(r: Router):
    r.shutdown.register(on_shutdown)
