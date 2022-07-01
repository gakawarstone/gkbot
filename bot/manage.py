from settings import ADMINS, TASKS_ON_STARTUP, bot
import handlers
from handlers.help import list_of_commands
from utils.notify import notify_admins


def start(bot=bot):
    bot.admins = ADMINS

    for task in TASKS_ON_STARTUP:
        bot.add_on_startup(task)

    bot.add_command_handler('list', list_of_commands)
    for cmd in handlers.users:
        bot.add_command_handler(cmd, handlers.users[cmd])
    for cmd in handlers.admins:
        bot.add_command_handler(cmd, handlers.admins[cmd], admin_only=True)
    for handler in handlers.channels:
        bot.add_channel_post_handler(handler)

    notify_admins('bot started')
    bot.start()
    notify_admins('bot stopped')
