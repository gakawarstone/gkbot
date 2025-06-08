from aiogram.fsm.state import State, StatesGroup


class _ChatGPTFSM(StatesGroup):
    finish = State()
    get_message = State()


FSM = _ChatGPTFSM
