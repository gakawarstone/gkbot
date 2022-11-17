from aiogram.fsm.state import State, StatesGroup


class _EditBookPropertyFSM(StatesGroup):
    get_new_value = State()
    finish = State()


FSM = _EditBookPropertyFSM
