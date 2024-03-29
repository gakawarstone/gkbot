from core.keyboard_builder import KeyboardBuilder
from .types import _Buttons


class MenuMarkup:
    buttons = _Buttons

    menu = KeyboardBuilder.add_keyboard(
        buttons=[
            [buttons.my_books, buttons.add_new_book, buttons.update_book],
            [buttons.delete_book, buttons.exit],
        ]
    )
