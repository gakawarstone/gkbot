from aiogram.fsm.state import State, StatesGroup


class _AddFeedFSM(StatesGroup):
    get_url = State()
    finish = State()


FSM = _AddFeedFSM
