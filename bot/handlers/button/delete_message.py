from aiogram.types import CallbackQuery, Message
from aiogram import Router, F

from ui.buttons.delete_message import deleteMessageButtonPrefix


async def delete_message(callback: CallbackQuery):
    if not isinstance(callback.message, Message):
        raise ValueError("Callback message is not of type Message")

    await callback.message.delete()


def setup(r: Router):
    r.callback_query.register(
        delete_message, F.data.startswith(deleteMessageButtonPrefix)
    )
