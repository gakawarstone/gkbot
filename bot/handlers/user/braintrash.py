from aiogram.types import Message
from aiogram.filters.command import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from settings import mng  # [ ] move add url button from BotManager
from lib.bot import BotManager
from filters.bot_admin import BotAdmin
from services.notion_api import Page
# [ ] move page id to settings | env
braintrash = Page('98997f76b28d48cb946d04e32b540e64')


class FSM(StatesGroup):
    write = State()
    get_message = State()
    get_all_data = State()
    finish = State()


async def write(message: Message, state: FSMContext):
    await state.set_state(FSM.get_message)
    await message.answer('Вы попали в свалку')
    await message.answer('Можете написать сюда все что захотите')


async def get_all_data(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    await message.answer('Вывод всего что находится в свалке')
    for i, title in enumerate(await braintrash.get_all_children_titles()):
        outp = str(i + 1) + ': ' + title + ('\n' * 2)
        await message.answer(outp)


async def get_message(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    await braintrash.write(message.text)
    btn = mng.add_url_button(await braintrash.get_url(), text='Ссылка')
    await message.answer('Информация сохранена', reply_markup=btn)


def setup(mng: BotManager):
    mng.add_state_handler(FSM.write, write)
    mng.add_state_handler(FSM.get_all_data, get_all_data)
    mng.add_state_handler(FSM.get_message, get_message)
    mng.dp.message.register(
        get_all_data,
        BotAdmin(),
        Command(commands='get_trash')
    )
