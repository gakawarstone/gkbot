from aiogram.fsm.state import State, StatesGroup


class _SortSourcesFSM(StatesGroup):
    sort_file = State()
    finish = State()


FSM = _SortSourcesFSM
