from typing import Type, Union

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ui.keyboards.bool import BoolMarkup
from utils.message import delete_previous_message
from .base import BaseHandler
from ..states import FSM

_Handler = Union[BaseHandler, Type[BaseHandler]]


async def ask_to_restart(callback: _Handler, text: str):
    callback.data['data']['callback'] = callback
    await callback.event.answer(text, reply_markup=BoolMarkup.yes_or_no)
    await callback.state.set_state(FSM.choose_bool)


async def choose_bool(message: Message, state: FSMContext, data: dict):
    await state.set_state(FSM.finish)
    await message.delete()
    await delete_previous_message(message, state)
    callback: _Handler = data['callback']
    if message.text in (BoolMarkup.buttons.yes, 'y'):
        await callback.handle()
