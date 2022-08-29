from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StateFilter, StatesGroup

from services.shiki import UserUpdatesDispatcher, InvalidUserException


class FSM(StatesGroup):
    subscribe = State()
    get_name = State()
    finish = State()


async def subscribe(message: Message, state: FSMContext):
    await state.set_state(FSM.get_name)
    await message.answer('ЭТО НОВЫЙ ПАТРЕ ЙОБАНЫЙ ЗОМАЙ')
    await message.answer('Пришли мне ник человека на shikimori.one')


async def get_name(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    try:
        await UserUpdatesDispatcher.add_subscription(
            chat_id=message.chat.id,
            shiki_name=message.text
        )
        await message.answer('Подписка оформлена')
    except InvalidUserException:
        await message.answer('Пользователь не найден')


def setup(r: Router):
    r.message.register(subscribe, StateFilter(state=FSM.subscribe))
    r.message.register(get_name, StateFilter(state=FSM.get_name))
