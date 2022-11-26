from aiogram import Router
from aiogram.filters import Command, and_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from lib.types import ChatType
from filters.chat_type import ChatTypeFilter


async def tag_all_admins(message: Message, state: FSMContext):
    chat_admins = await state.bot.get_chat_administrators(message.chat.id)
    await message.answer(' '.join([f'@{admin.user.username}'
                                   for admin in chat_admins]))


def setup(r: Router):
    r.message.register(tag_all_admins, and_f(
        Command(commands=['admins']),
        ChatTypeFilter(chat_type=[ChatType.group, ChatType.super_group])
    ))
