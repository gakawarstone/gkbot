from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import Message

from ui.keyboards.bool import BoolMarkup


async def ask_confirmation(
    message: Message,
    state: FSMContext,
    data: dict[str, Any],
    text: str,
    on_yes: Callable[[], Awaitable[Any]],
    waiting_state: State,
    finished_state: State,
    on_no: Callable[[], Awaitable[Any]] | None = None,
) -> None:
    prompt = await message.answer(text, reply_markup=BoolMarkup.yes_or_no)
    data["delete_queue"].append(prompt)
    await state.set_state(waiting_state)
    data["confirmation"] = (on_yes, on_no, finished_state)


async def choose_bool(
    message: Message, state: FSMContext, data: dict[str, Any]
) -> None:
    confirmation = data.pop("confirmation", None)
    if confirmation is None:
        return
    on_yes, on_no, finished_state = confirmation
    await state.set_state(finished_state)
    await message.delete()
    if message.text in (BoolMarkup.buttons.yes, "y"):
        await on_yes()
    elif message.text == BoolMarkup.buttons.no and on_no is not None:
        await on_no()
