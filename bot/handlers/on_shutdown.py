from aiogram import Router
from tortoise import Tortoise

from services.gkfeed.api import GkfeedApi
from services.http import HttpService
from services.schedule import Schedule


async def on_shutdown() -> None:
    try:
        await GkfeedApi.on_shutdown()
        await Schedule.on_shutdown()
        await Tortoise.close_connections()
    finally:
        await HttpService.close()


def setup(r: Router) -> None:
    r.shutdown.register(on_shutdown)
