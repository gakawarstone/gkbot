from aiogram import F, Router
from aiogram.filters.state import StateFilter
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from services.timer import TimersManager
from ui.keyboards.timer import TimerMarkup
from ui.components.timer import TimerComponent
from ._commands import USER_COMMANDS


F: CallbackQuery


class FSM(StatesGroup):
    start_timer = State()
    get_timer_name = State()
    finish = State()


async def start_timer(message: Message, state: FSMContext):
    await message.delete()
    await message.answer('Введите название таймера')
    await state.set_state(FSM.get_timer_name)


async def get_timer_name(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    TimersManager.get_or_create_timer(
        f'{message.from_user.id}:{message.text}'
    ).start()
    await message.answer(
        TimerComponent.serialize_start_message(
            timer_name=message.text
        ),
        reply_markup=TimerMarkup.get_timer_dialog(message.text)
    )


async def stop_timer(callback: CallbackQuery):
    timer_name = callback.data.split(':')[1]
    timer_id = f'{callback.from_user.id}:{timer_name}'
    timer = TimersManager.get_timer_by_id(timer_id)
    timer.stop()
    TimersManager.delete_timer_by_id(timer_id)

    await callback.message.edit_text(
        TimerComponent.serialize_data_message(
            timer_name=timer_name,
            start_time_rfc2882=timer.start_time_rfc2882,
            finish_time_rfc2882=timer.finish_time_rfc2882,
            time_delta=timer.time_delta
        )
    )


def setup(r: Router):
    r.message.register(
        start_timer,
        Command(commands=USER_COMMANDS.start_timer)
    )
    r.message.register(
        get_timer_name,
        StateFilter(FSM.get_timer_name)
    )
    r.callback_query.register(
        stop_timer,
        F.data.startswith('stop_timer')
    )
