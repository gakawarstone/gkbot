from settings import ADMINS, TASKS_ON_STARTUP, bot
from handlers.setup import setup_handlers
from utils.notify import notify_admins


def start(bot=bot):
    bot.admins = ADMINS

    # [ ] bot.add_tasks_on_startup()
    for task in TASKS_ON_STARTUP:
        bot.add_on_startup(task)

    setup_handlers(bot)

    notify_admins('bot started')
    bot.start()
    notify_admins('bot stopped')
