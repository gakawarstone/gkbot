from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from ui.buttons.delete_message import deleteMessageButtonPrefix


async def delete_message(callback: CallbackQuery):
    if not isinstance(callback.message, Message):
        raise TypeError("Callback message is not of type Message")

    await callback.message.delete()


def setup(r: Router):
    r.callback_query.register(
        delete_message, F.data.startswith(deleteMessageButtonPrefix)
    )
