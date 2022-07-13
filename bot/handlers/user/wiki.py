import logging

from aiogram.types import Message
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from lib.bot import BotManager

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
        await message.answer('Нашел кое-что 👇\n\n' + quote)
    else:
        await message.answer('Я ничего не нашел 🙂')


def setup(mng: BotManager):
    mng.add_state_handler(FSM.search, search)
    mng.add_state_handler(FSM.get_data, get_data)
