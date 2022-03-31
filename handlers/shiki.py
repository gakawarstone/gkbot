import aiogram
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from bot_config import bot, admins
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
            await message.answer(
                '''
                <b>%s</b>\n[<i>%s</i>]\nПользователь <a href="%s">@%s</a>
                ''' %
                (update.name_ru,
                 update.type,
                 user.url,
                 message.text,)
            )
    except(Exception):
        await message.answer('Пользователь не найден')


async def subscribe(message: aiogram.types.Message):
    dp = shiki.UserUpdatesDispatcher()
    dp.add_subscription(admins[0], 'gakawarstone')
    print(dp.subscriptions)



class FSM(StatesGroup):
    get_from_shiki = State()
