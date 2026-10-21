from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from configs.commands import USER_COMMANDS


async def exit_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Режим завершён. Обычный режим бота снова активен.",
        reply_markup=ReplyKeyboardRemove(),
    )


def setup(router: Router) -> None:
    router.message.register(exit_flow, Command(USER_COMMANDS.exit))
