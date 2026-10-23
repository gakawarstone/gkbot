from aiogram import Router
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from middlewares.data import UserData
from ui.keyboards.road import RoadMarkup

from .habits import habit_tracker
from .pomodoro import PomodoroHandler
from .settings.start import InitSettingsHandler
from .states import FSM


async def choose_tool(message: Message, state: FSMContext, data: UserData) -> None:
    await state.set_state(FSM.finish)
    await message.delete()
    match message.text:
        case RoadMarkup.buttons.pomodoro | "1":
            await PomodoroHandler(message, state=state, data=data)
        case RoadMarkup.buttons.habit_tracker | "2":
            await habit_tracker(message, state)
        case RoadMarkup.buttons.settings | "3":
            await InitSettingsHandler(message, state=state, data=data)


def setup(r: Router):
    r.message.register(choose_tool, StateFilter(FSM.menu))
