from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ._commands import USER_COMMANDS


async def list_of_commands(message: Message):
    text = 'Привет вот список команд которые есть в боте:\n\n'
    for cmd in USER_COMMANDS.as_list():
        text += '/%s\n' % cmd
    await message.answer(text)


def setup(r: Router):
    r.message.register(list_of_commands, Command(commands=USER_COMMANDS.list))
