from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup

from services.wiki import WikiApi, QuoteNotFound

from configs.commands import USER_COMMANDS


class FSM(StatesGroup):
    search = State()
    get_data = State()
    finish = State()


async def search(message: Message, state: FSMContext):
    await state.set_state(FSM.get_data)
    await message.delete()
    await message.answer("Что будем <b>искать</b> 🧐?")


async def get_data(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    await message.delete()

    if message.text is None:
        raise ValueError("Message text is None")

    try:
        quote = WikiApi.get_quote(message.text)
        await message.answer(
            f"Нашел кое-что по запросу <b>{message.text}</b> 👇\n\n" + quote
        )
    except QuoteNotFound:
        await message.answer("Я ничего не нашел 🙂")


def setup(r: Router):
    r.message.register(search, StateFilter(FSM.search))
    r.message.register(get_data, StateFilter(FSM.get_data))
    r.message.register(search, Command(commands=USER_COMMANDS.wiki))
