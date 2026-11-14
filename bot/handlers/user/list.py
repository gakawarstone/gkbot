from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from configs.commands import USER_COMMANDS


async def list_of_commands(message: Message) -> None:
    text = "Привет вот список команд которые есть в боте:\n\n"
    text += "".join(f"/{command}\n" for command in USER_COMMANDS.as_list())
    await message.answer(text)


def setup(r: Router) -> None:
    r.message.register(list_of_commands, Command(commands=USER_COMMANDS.list))
