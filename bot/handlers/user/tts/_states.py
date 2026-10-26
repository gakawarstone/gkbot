from aiogram.fsm.state import State, StatesGroup


class _TTSFSM(StatesGroup):
    send_speech = State()
    finish = State()


FSM = _TTSFSM
