from aiogram import Router
from aiogram.filters import StateFilter, Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ui.static import Images
from ui.keyboards.road import RoadMarkup
from configs.commands import USER_COMMANDS
from .states import FSM


async def start(message: Message, state: FSMContext):
    await state.set_state(FSM.menu)

    # Check if message.from_user is not None
    first_name = "пользователь"
    if message.from_user and message.from_user.first_name:
        first_name = message.from_user.first_name

    await message.answer_photo(
        await Images.road_greet.as_input_file(),
        caption=f"Привет <i>{first_name}</i> ты включил модуль 🚀<b>РОД ЗЕ ДРИМ</b>🚀",
    )
    await message.answer(
        "Пожалуйста выберите 🛠 <b>инструмент</b>", reply_markup=RoadMarkup.tools
    )


def setup(r: Router):
    r.message.register(
        start, or_f(StateFilter(FSM.start), Command(commands=USER_COMMANDS.road))
    )
