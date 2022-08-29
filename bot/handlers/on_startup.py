from aiogram import Router

from utils.notify import Notifier


async def on_startup():
    await Notifier.notify_admins('bot started')


def setup(r: Router):
    r.startup.register(on_startup)
