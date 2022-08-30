import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StateFilter, StatesGroup

from services.wiki import WikiApi

logger = logging.getLogger(__name__)


class FSM(StatesGroup):
    search = State()
    get_data = State()
    finish = State()


async def search(message: Message, state: FSMContext):
    await state.set_state(FSM.get_data)
    await message.delete()
    await message.answer('Что будем <b>искать</b> 🧐?')


async def get_data(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    await message.delete()
    if quote := WikiApi.get_quote(message.text):
        await message.answer('Нашел кое-что по запросу <b>%s</b> 👇\n\n' %
                             message.text + quote)
    else:
        await message.answer('Я ничего не нашел 🙂')


def setup(r: Router):
    r.message.register(search, StateFilter(state=FSM.search))
    r.message.register(get_data, StateFilter(state=FSM.get_data))
