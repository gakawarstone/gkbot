from aiogram.fsm.state import StatesGroup, State


class _TTSFSM(StatesGroup):
    send_speech = State()
    finish = State()


FSM = _TTSFSM
