from aiogram import Router, Dispatcher

from . import user
from . import text
from . import inline
from . import on_startup
from . import error
from . import prompt
from . import button


def setup(dp: Dispatcher):
    r = dp.include_router(Router())
    user.setup(r)
    text.setup(r)
    inline.setup(r)
    on_startup.setup(r)
    error.setup(r)
    prompt.setup(r)
    button.setup(r)
