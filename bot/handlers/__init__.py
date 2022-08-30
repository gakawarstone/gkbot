from aiogram import Router, Dispatcher

from . import commands
from . import user
from . import text
from . import inline
from . import help
from . import on_startup


def setup(dp: Dispatcher):
    r = dp.include_router(Router())
    user.setup(r)
    commands.setup(r)
    text.setup(r)
    inline.setup(r)
    help.setup(r)
    on_startup.setup(r)
