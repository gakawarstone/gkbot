from bot_config import admins, bot, schedule
from lib.shiki import UserUpdatesDispatcher
import handlers
from handlers.help import list_of_commands
from utils.notify import notify_admins


def start():
    bot.admins = admins
    bot.add_on_startup(schedule.on_startup)
    bot.add_on_startup(UserUpdatesDispatcher().on_startup)
    bot.add_command_handler('list', list_of_commands)
    for cmd in handlers.users:
        bot.add_command_handler(cmd, handlers.users[cmd])
    for cmd in handlers.admins:
        bot.add_command_handler(cmd, handlers.admins[cmd], admin_only=True)
    notify_admins('bot started')
    bot.start()
    notify_admins('bot stopped')
