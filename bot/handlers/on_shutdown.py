from aiogram import Router
from tortoise import Tortoise

from services.gkfeed.api import GkfeedApi
from services.schedule import Schedule
from workers.feed_parser import feed_parser


async def on_shutdown() -> None:
    await feed_parser.close()
    await GkfeedApi.on_shutdown()
    await Schedule.on_shutdown()
    await Tortoise.close_connections()


def setup(r: Router) -> None:
    r.shutdown.register(on_shutdown)
