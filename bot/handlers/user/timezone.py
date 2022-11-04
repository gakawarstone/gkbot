from datetime import timedelta

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter, State, StatesGroup
from services.timezone import TimeZone, InvalidTimeZone
from aiogram.filters import Command


class FSM(StatesGroup):
    set_timezone = State()
    finish = State()


async def init_timezone_set(message: Message, state: FSMContext):
    await state.set_state(FSM.set_timezone)
    await message.answer('Введите число от -12 до +14:')


async def _set_timezone(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    try:
        tz = timedelta(hours=int(message.text))
        await TimeZone.set_user_timezone(message.from_user.id, tz)
        await message.answer('Таймзона установлена')
    except (InvalidTimeZone, ValueError):
        await state.set_state(FSM.set_timezone)
        await message.answer('Таймзона должна быть от -12 до 14')


def setup(r: Router):
    r.message.register(init_timezone_set, Command(commands='set_tz'))
    r.message.register(_set_timezone, StateFilter(state=FSM.set_timezone))
