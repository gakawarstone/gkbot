from aiogram import F, Router
from aiogram.filters import StateFilter, or_f

from ui.keyboards.chat import ChatMarkup

from ..exit import exit_flow
from ._states import FSM


def setup(router: Router) -> None:
    router.message.register(
        exit_flow,
        StateFilter(FSM.get_message),
        or_f(
            F.text == ChatMarkup.buttons.exit,
            F.text.casefold() == "q",
        ),
    )
