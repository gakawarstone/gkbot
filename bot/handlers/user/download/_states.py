from aiogram.filters.state import State, StatesGroup


class _DownloadFSM(StatesGroup):
    finish = State()
    get_name = State()
    get_link = State()


FSM = _DownloadFSM
