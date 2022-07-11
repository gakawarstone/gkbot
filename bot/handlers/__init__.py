from . import commands
from . import user
import logging
from .help import list_of_commands
from lib.bot import BotManager


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

channels = [
    # chnnel.echo_post,
]


def setup(mng: BotManager):
    user.setup(mng)
    commands.setup(mng)
    mng.add_command_handler('list', list_of_commands)

    for handler in channels:
        mng.add_channel_post_handler(handler)
