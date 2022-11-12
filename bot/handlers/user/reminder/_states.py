from aiogram.fsm.state import State, StatesGroup


class FSM(StatesGroup):
    start = State()
    get_text = State()
    get_date = State()
    get_time = State()
    finish = State()
