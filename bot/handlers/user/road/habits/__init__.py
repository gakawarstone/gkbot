from datetime import datetime

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from middlewares.data import UserData
from models.road import Habits  # FIXME

from ..states import FSM


async def habit_tracker(message: Message, state: FSMContext):
    await state.set_state(FSM.get_habit_name)
    await message.answer(
        "Вы включили трекер привычек", reply_markup=ReplyKeyboardRemove()
    )
    await message.answer("<b>Поздравляю</b> вы получили 🦣")
    await message.answer(
        "Ладно заскамленное животное давай попробуем добавить привычку"
    )
    await message.answer(
        "Пришли мне название привычки которую мы с тобой будем прививать"
    )


async def get_habit_name(message: Message, state: FSMContext, data: UserData) -> None:
    await state.set_state(FSM.get_habit_notify_time)
    data["habit_name"] = message.text
    await message.answer(
        "Теперь пришли время в которое я буду спрашивать тебя об успехах"
    )


async def get_habit_notify_time(
    message: Message, state: FSMContext, data: UserData
) -> None:
    await state.set_state(FSM.finish)

    if message.text is None:
        raise ValueError("message must not be None")

    if message.from_user is None:
        raise ValueError("message.from_user must not be None")

    habit_name = data.get("habit_name")
    if habit_name is None:
        raise ValueError("habit_name must be set before choosing the notify time")

    time = datetime.strptime(message.text, "%H:%M").time()
    data["habit_notify_time"] = time

    await Habits.create(
        user_id=message.from_user.id,
        name=habit_name,
        notify_time=data["habit_notify_time"],
    )
    await message.answer("Привычка добавлена")


def setup(r: Router):
    r.message.register(get_habit_name, StateFilter(FSM.get_habit_name))
    r.message.register(get_habit_notify_time, StateFilter(FSM.get_habit_notify_time))
