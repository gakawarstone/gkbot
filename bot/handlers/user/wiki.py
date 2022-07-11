import logging

import wikipedia
from aiogram.types import Message
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from lib.bot import BotManager


logger = logging.getLogger(__name__)


class FSM(StatesGroup):
    search = State()
    get_data = State()
    finish = State()


async def search(message: Message, state: FSMContext):
    await state.set_state(FSM.get_data)
    await message.answer('Привет ты включил <b>новую и оригинальную</b> функцию')
    await message.answer('Пришли мне то о чем ты хочешь получить информация из википедии')


async def get_data(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    wikipedia.set_lang("ru")
    try:
        quote = wikipedia.summary(message.text, sentences=4)
        await message.answer(quote)
    except Exception as e:
        logger.info(e)
        await message.answer('Извините но я ничего не нашел')


def setup(mng: BotManager):
    mng.add_state_handler(FSM.search, search)
    mng.add_state_handler(FSM.get_data, get_data)
