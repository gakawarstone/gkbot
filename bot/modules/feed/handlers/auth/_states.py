from aiogram.fsm.state import State, StatesGroup


class FSM(StatesGroup):
    get_login = State()
    get_password = State()
    finish = State()
