from lib.bot import BotManager
from . import commands
from . import user
from . import text
from . import inline
from .help import list_of_commands


channels = [
    # chnnel.echo_post,
]


def setup(mng: BotManager):
    user.setup(mng)
    commands.setup(mng)
    text.setup(mng)
    inline.setup(mng)

    mng.add_command_handler('list', list_of_commands)

    for handler in channels:
        mng.add_channel_post_handler(handler)
