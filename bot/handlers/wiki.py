import logging

import aiogram
import wikipedia
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from settings import bot

logger = logging.getLogger(__name__)


async def search(message: aiogram.types.Message):
    await message.answer('Привет ты включил <b>новую и оригинальную</b> функцию')
    await message.answer('Пришли мне то о чем ты хочешь получить информация из википедии')
    bot.add_state_handler(FSM.get_data, get_data)
    await FSM.get_data.set()


async def get_data(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    wikipedia.set_lang("ru")
    try:
        quote = wikipedia.summary(message.text, sentences=4)
        await message.answer(quote)
    except Exception as e:
        logger.info(e)
        await message.answer('Извините но я ничего не нашел')


class FSM(StatesGroup):
    get_data = State()
