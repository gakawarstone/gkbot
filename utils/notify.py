import asyncio

from bot_config import bot, admins


def notify_admins(text: str):
    loop = asyncio.get_event_loop()
    for admin_id in admins:
        loop.run_until_complete(bot.send_message(admin_id, text))
