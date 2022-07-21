from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message

from lib.bot import BotManager
from lib.types import ChatType
from filters.chat_type import ChatTypeFilter


async def tag_all_admins(message: Message, state: FSMContext):
    chat_admins = await state.bot.get_chat_administrators(message.chat.id)
    await message.answer(' '.join([f'@{admin.user.username}'
                                   for admin in chat_admins]))


def setup(mng: BotManager):
    mng.dp.register_message(
        tag_all_admins,
        ChatTypeFilter(chat_type=[ChatType.group, ChatType.super_group]),
        Command(commands=['admins'])
    )
