from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup


from lib.bot import BotManager
from services.shiki.user_updates import User


class FSM(StatesGroup):
    get_updates = State()
    get_from_shiki = State()
    finish = State()


async def get_updates(message: Message, state: FSMContext):
    await state.set_state(FSM.get_from_shiki)
    await message.delete()
    await message.answer('Пришли мне ник человека на shikimori.one')


async def get_from_shiki(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    user = User(message.text)
    try:
        for update in await user.updates.load_latest(10):
            await message.answer(str(update) + str(user))
    except KeyError:
        await message.answer('Пользователь не найден')


def setup(mng: BotManager):
    mng.add_state_handler(FSM.get_updates, get_updates)
    mng.add_state_handler(FSM.get_from_shiki, get_from_shiki)
