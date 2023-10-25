from aiogram import Router

from core.notifier import Notifier
from configs.admins import ADMINS


async def on_startup():
    [await Notifier.notify(admin, "bot started") for admin in ADMINS]


def setup(r: Router):
    r.startup.register(on_startup)
