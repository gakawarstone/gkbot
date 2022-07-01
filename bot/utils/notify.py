import asyncio

from settings import bot, ADMINS


def notify_admins(text: str):
    loop = asyncio.get_event_loop()
    for admin_id in ADMINS:
        loop.run_until_complete(bot.send_message(admin_id, text))
