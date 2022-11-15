from aiogram.fsm.state import State, StatesGroup


class FSM(StatesGroup):
    show_menu = State()
    check_menu_command = State()
    show_my_books = State()
    finish = State()
    show_test_book = State()
    change_book_property = State()
