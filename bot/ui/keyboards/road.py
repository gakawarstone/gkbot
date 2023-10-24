from dataclasses import dataclass

from core.keyboard_builder import KeyboardBuilder


@dataclass
class _Buttons:
    pomodoro = "🕔 Помидор"
    habit_tracker = "Трекер привычек"
    settings = "⚙️  Настройки"


class RoadMarkup:
    buttons = _Buttons

    tools = KeyboardBuilder.add_keyboard(
        buttons=[[_Buttons.pomodoro, _Buttons.habit_tracker], [_Buttons.settings]]
    )
