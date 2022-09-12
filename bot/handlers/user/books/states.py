from aiogram.fsm.state import State, StatesGroup


class FSM(StatesGroup):
    show_menu = State()
    check_menu_command = State()
    get_new_book_name = State()
    show_my_books = State()
    finish = State()
    show_test_book = State()
    get_new_book_author = State()
    get_new_book_chapters_cnt = State()
