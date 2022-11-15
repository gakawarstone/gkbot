from aiogram.fsm.state import State, StatesGroup


class AddBookFSM(StatesGroup):
    get_name = State()
    get_author = State()
    get_chapters_cnt = State()
    finish = State()
