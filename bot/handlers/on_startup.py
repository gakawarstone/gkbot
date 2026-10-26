from aiogram import Router

from core.notifier import Notifier


async def on_startup(admins: list[int]) -> None:
    for admin in admins:
        await Notifier.notify(admin, "bot started")


def setup(r: Router):
    r.startup.register(on_startup)
