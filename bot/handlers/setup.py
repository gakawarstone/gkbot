from lib.bot import BotManager
from .help import list_of_commands
from . import users, admins, channels


def setup_handlers(mng: BotManager):
    mng.add_command_handler('list', list_of_commands)
    for cmd in users.items():
        mng.add_command_handler(*cmd)
    for cmd in admins:
        mng.add_command_handler(cmd, admins[cmd], admin_only=True)
    for handler in channels:
        mng.add_channel_post_handler(handler)
