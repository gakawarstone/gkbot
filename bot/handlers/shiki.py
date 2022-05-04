import aiogram
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from bot_config import bot
from lib import shiki


async def get_updates(message: aiogram.types.Message):
    await message.answer('Привет это бета версия так что вывод информции немного некрасивый')
    await message.answer('Пришли мне ник человека на shikimori.one')
    bot.add_state_handler(FSM.get_from_shiki, get_from_shiki)
    await FSM.get_from_shiki.set()


async def get_from_shiki(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    user = shiki.User(message.text)
    try:
        for update in user.updates.load_latest(10):
            await message.answer(str(update) + str(user))
    except(Exception):
        await message.answer('Пользователь не найден')


async def subscribe(message: aiogram.types.Message):
    await message.answer('ЭТО НОВЫЙ ПАТРЕ ЙОБАНЫЙ ЗОМАЙ')
    await message.answer('Пришли мне ник человека на shikimori.one')
    bot.add_state_handler(FSM.get_name, get_name)
    await FSM.get_name.set()


async def get_name(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    dp = shiki.UserUpdatesDispatcher()
    dp.add_subscription(message.chat.id, message.text)
    await message.answer('Подписка оформлена')


class FSM(StatesGroup):
    get_from_shiki = State()
    get_name = State()
