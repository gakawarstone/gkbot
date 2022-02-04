from bot_config import admins, bot, schedule
import handlers
from handlers.help import help
from utils.notify import notify_admins


def start():
    bot.admins = admins
    bot.add_task(schedule.on_startup)
    bot.add_command_handler('help', help)
    for cmd in handlers.users:
        bot.add_command_handler(cmd, handlers.users[cmd])
    for cmd in handlers.admins:
        bot.add_command_handler(cmd, handlers.admins[cmd], admin_only=True)
    notify_admins('bot started')
    bot.start()
    notify_admins('bot stopped')
