from aiogram import Router

from configs import db
from services.gkfeed.api import GkfeedApi
from services.schedule import Schedule


async def on_shutdown() -> None:
    await GkfeedApi.on_shutdown()
    await Schedule.on_shutdown()
    await db.on_shutdown()


def setup(r: Router) -> None:
    r.shutdown.register(on_shutdown)
