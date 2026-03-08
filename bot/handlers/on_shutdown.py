from aiogram import Router
from configs import db


async def on_shutdown():
    await db.on_shutdown()


def setup(r: Router):
    r.shutdown.register(on_shutdown)
