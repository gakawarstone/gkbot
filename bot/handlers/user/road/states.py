from aiogram.fsm.state import State, StatesGroup


class _RoadFSM(StatesGroup):
    start = State()
    menu = State()
    pomodoro = State()
    choose_bool = State()
    get_habit_name = State()
    get_habit_notify_time = State()
    get_new_setting_value = State()
    finish = State()


FSM = _RoadFSM
