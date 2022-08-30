from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StateFilter, StatesGroup


from services.shiki import User, InvalidUserException


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
    except InvalidUserException:
        await message.answer('Пользователь не найден')


def setup(r: Router):
    r.message.register(get_updates, StateFilter(state=FSM.get_updates))
    r.message.register(get_from_shiki, StateFilter(state=FSM.get_from_shiki))
