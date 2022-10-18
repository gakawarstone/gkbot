from aiogram.fsm.context import FSMContext
from aiogram.types import Message


async def delete_previous_message(message: Message, state: FSMContext):
    await state.bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.message_id - 1
    )
