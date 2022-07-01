from lib.bot import Bot
from .help import list_of_commands
from . import users, admins, channels


def setup_handlers(bot: Bot):
    bot.add_command_handler('list', list_of_commands)
    for cmd in users:
        bot.add_command_handler(cmd, users[cmd])
    for cmd in admins:
        bot.add_command_handler(cmd, admins[cmd], admin_only=True)
    for handler in channels:
        bot.add_channel_post_handler(handler)
