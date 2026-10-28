from aiogram import Bot, Router
from aiogram.filters import Command, and_f
from aiogram.types import Message

from configs.commands import USER_COMMANDS
from core.types import ChatType
from filters.chat_type import ChatTypeFilter


async def tag_all_admins(message: Message, bot: Bot) -> None:
    chat_admins = await bot.get_chat_administrators(message.chat.id)
    await message.answer(" ".join([f"@{admin.user.username}" for admin in chat_admins]))


def setup(r: Router) -> None:
    r.message.register(
        tag_all_admins,
        and_f(
            Command(commands=USER_COMMANDS.admins),
            ChatTypeFilter(chat_type=[ChatType.group, ChatType.super_group]),
        ),
    )
