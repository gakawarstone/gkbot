from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from middlewares.data import RestartableHandler, UserData
from ui.keyboards.bool import BoolMarkup

from ..states import FSM

# TODO: move to extensions


async def ask_to_restart(callback: RestartableHandler, text: str) -> None:
    callback.user_data["callback"] = callback
    mes = await callback.event.answer(text, reply_markup=BoolMarkup.yes_or_no)
    callback.user_data["delete_queue"].append(mes)
    await callback.state.set_state(FSM.choose_bool)


async def choose_bool(message: Message, state: FSMContext, data: UserData) -> None:
    await state.set_state(FSM.finish)
    await message.delete()
    callback = data.get("callback")
    if callback is None:
        raise RuntimeError("No handler is waiting for restart")
    if message.text in (BoolMarkup.buttons.yes, "y"):
        await callback.handle()
