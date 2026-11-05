import re
from datetime import datetime
from typing import Any

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from models.road import Habits

from ..states import FSM


async def habit_tracker(message: Message, state: FSMContext) -> None:
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


async def get_habit_name(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Пришли непустое название привычки")
        return

    data["habit_name"] = name
    await state.set_state(FSM.get_habit_notify_time)
    await message.answer(
        "Теперь пришли время в которое я буду спрашивать тебя об успехах"
    )


async def get_habit_notify_time(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    text = message.text or ""
    try:
        if not re.fullmatch(r"[0-9]{2}:[0-9]{2}", text):
            raise ValueError
        time = datetime.strptime(text, "%H:%M").time()
    except ValueError:
        await message.answer("Пришли корректное время в формате ЧЧ:ММ")
        return

    if message.from_user is None:
        raise ValueError("message.from_user must not be None")

    await Habits.create(
        user_id=message.from_user.id,
        name=data["habit_name"],
        notify_time=time,
    )
    await state.set_state(FSM.finish)
    await message.answer("Привычка добавлена")


def setup(r: Router) -> None:
    r.message.register(get_habit_name, StateFilter(FSM.get_habit_name))
    r.message.register(get_habit_notify_time, StateFilter(FSM.get_habit_notify_time))
