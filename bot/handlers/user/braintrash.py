from aiogram import Router
from aiogram.types import Message
from aiogram.filters import and_f
from aiogram.filters.command import Command
from aiogram.filters.state import State, StateFilter, StatesGroup
from aiogram.fsm.context import FSMContext

from filters.bot_admin import BotAdmin
from services.notion_api import Page
from ui.keyboards.url_button import UrlButtonMarkup
from ._commands import USER_COMMANDS

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
    markup = UrlButtonMarkup.get(url=await braintrash.get_url(), text='Ссылка')
    await message.answer('Информация сохранена', reply_markup=markup)


def setup(r: Router):
    r.message.register(write, StateFilter(FSM.write))
    r.message.register(get_all_data, StateFilter(FSM.get_all_data))
    r.message.register(get_message, StateFilter(FSM.get_message))
    r.message.register(get_all_data, and_f(
        Command(commands=USER_COMMANDS.get_trash),
        BotAdmin()
    ))  # [ ] admin command
    r.message.register(write, Command(commands=USER_COMMANDS.trash))
