from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from configs.commands import USER_COMMANDS


async def exit_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    response = message.answer(
        "Режим завершён. Обычный режим бота снова активен.",
        reply_markup=ReplyKeyboardRemove(),
    )
    response.message_thread_id = message.message_thread_id
    await response


def setup(router: Router) -> None:
    router.message.register(exit_flow, Command(USER_COMMANDS.exit))
