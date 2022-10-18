from lib.keyboard_builder import KeyboardBuilder


class _Buttons:
    yes = 'Да'
    no = 'Нет'


class BoolMarkup:
    buttons = _Buttons

    yes_or_no = KeyboardBuilder.add_keyboard(
        buttons=[
            [_Buttons.yes, _Buttons.no]
        ]
    )
