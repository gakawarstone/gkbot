from typing import Type, Union

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from extensions.handlers.message.base import BaseHandler
from ui.keyboards.bool import BoolMarkup

from ..states import FSM

_Handler = Union[BaseHandler, Type[BaseHandler]]

# TODO: move to contrib


async def ask_to_restart(callback: _Handler, text: str):
    callback.data["data"]["callback"] = callback
    mes = await callback.event.answer(text, reply_markup=BoolMarkup.yes_or_no)
    callback.data["data"]["delete_queue"].append(mes)
    await callback.state.set_state(FSM.choose_bool)


async def choose_bool(message: Message, state: FSMContext, data: dict):
    await state.set_state(FSM.finish)
    await message.delete()
    callback: _Handler = data["callback"]
    if message.text in (BoolMarkup.buttons.yes, "y"):
        await callback.handle()
