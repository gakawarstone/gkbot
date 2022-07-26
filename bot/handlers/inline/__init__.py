from aiogram import Router

from lib.bot import BotManager
from . import tiktok

router = Router()


def setup(mng: BotManager):
    tiktok.setup(router)
    mng.dp.include_router(router)
