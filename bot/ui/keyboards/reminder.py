from dataclasses import dataclass

from lib.keyboard_builder import KeyboardBuilder


@dataclass
class _Buttons:
    today = 'Сегодня'
    tomorrow = 'Завтра'


class RemindMarkup:
    buttons = _Buttons

    date = KeyboardBuilder.add_keyboard(
        buttons=[
            [buttons.today, buttons.tomorrow]
        ]
    )
