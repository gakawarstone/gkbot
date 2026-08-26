from core.keyboard_builder import KeyboardBuilder


class _Buttons:
    exit = "🚪 Выйти из AI-чата"


class ChatMarkup:
    buttons = _Buttons

    menu = KeyboardBuilder.add_keyboard(
        buttons=[[buttons.exit]],
        hide=False,
        placeholder="Сообщение для AI",
    )
