from aiogram.fsm.state import State, StatesGroup


class _Platonus2IndigoFSM(StatesGroup):
    convert = State()
    finish = State()


FSM = _Platonus2IndigoFSM
