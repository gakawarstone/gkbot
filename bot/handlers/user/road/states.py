from aiogram.filters.state import State, StatesGroup


class _RoadFSM(StatesGroup):
    start = State()
    choose_tool = State()
    pomodoro = State()
    choose_bool = State()
    get_habit_name = State()
    get_habit_notify_time = State()
    finish = State()


FSM = _RoadFSM
