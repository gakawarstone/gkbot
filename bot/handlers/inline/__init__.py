from aiogram import Router

from lib.bot import BotManager
from . import tiktok, youtube

router = Router()


def setup(mng: BotManager):
    tiktok.setup(router)
    youtube.setup(router)
    mng.dp.include_router(router)
