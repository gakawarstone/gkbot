from aiogram import Dispatcher, Router

from . import button, error, inline, on_shutdown, on_startup, prompt, text, user


def setup(dp: Dispatcher):
    r = dp.include_router(Router())
    user.setup(r)
    text.setup(r)
    inline.setup(r)
    on_startup.setup(r)
    error.setup(r)
    prompt.setup(r)
    button.setup(r)
    on_shutdown.setup(r)
