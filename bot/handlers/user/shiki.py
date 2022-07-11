from aiogram.types import Message
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from lib.bot import BotManager

from services import shiki


class FSM(StatesGroup):
    get_updates = State()
    subscribe = State()
    get_from_shiki = State()
    get_name = State()
    finish = State()


async def get_updates(message: Message, state: FSMContext):
    await state.set_state(FSM.get_from_shiki)
    await message.answer('Привет это бета версия так что вывод информции немного некрасивый')
    await message.answer('Пришли мне ник человека на shikimori.one')


async def get_from_shiki(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    user = shiki.User(message.text)
    try:  # BUG
        for update in user.updates.load_latest(10):
            await message.answer(str(update) + str(user))
    except(Exception):
        await message.answer('Пользователь не найден')


async def subscribe(message: Message, state: FSMContext):
    await state.set_state(FSM.get_name)
    await message.answer('ЭТО НОВЫЙ ПАТРЕ ЙОБАНЫЙ ЗОМАЙ')
    await message.answer('Пришли мне ник человека на shikimori.one')


async def get_name(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)  # [ ] if user invalid
    dp = shiki.UserUpdatesDispatcher()
    dp.add_subscription(message.chat.id, message.text)
    await message.answer('Подписка оформлена')


def setup(mng: BotManager):
    mng.add_state_handler(FSM.get_updates, get_updates)
    mng.add_state_handler(FSM.get_from_shiki, get_from_shiki)
    mng.add_state_handler(FSM.subscribe, subscribe)
    mng.add_state_handler(FSM.get_name, get_name)
