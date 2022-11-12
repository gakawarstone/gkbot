from aiogram.fsm.context import FSMContext
from aiogram.types import Message

# FIXME deprecated use delete queue middleware with one time message
# FIXME handler extension


async def delete_previous_message(message: Message, state: FSMContext):
    await state.bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.message_id - 1
    )
