from bot_config import admins, bot, schedule
from lib.shiki import UserUpdatesDispatcher
import handlers
from handlers.help import list_of_commands
from utils.notify import notify_admins
from utils.commands import DefaultCommands

default_commands = {
    'list': 'list of possible bot commands',
    'road': 'road to the dream',
    'bomber': 'use it for call someone',
    'add_remind': 'add remind',
    'start_timer': 'start timer',
}

tasks_on_startup = [
    DefaultCommands.set(default_commands).on_startup,
    schedule.on_startup,
    UserUpdatesDispatcher().on_startup,
]


def start(bot=bot):
    bot.admins = admins

    for task in tasks_on_startup:
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
