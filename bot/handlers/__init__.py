from aiogram import Router, Dispatcher

from . import user
from . import text
from . import inline
from . import on_startup


def setup(dp: Dispatcher):
    r = dp.include_router(Router())
    user.setup(r)
    text.setup(r)
    inline.setup(r)
    on_startup.setup(r)
