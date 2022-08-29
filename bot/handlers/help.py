from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from .commands import users


async def list_of_commands(message: Message):
    # NOTE r.message.handlers
    text = 'Привет вот список команд которые есть в боте:\n\n'
    for cmd in users:
        text += '/%s\n' % cmd
    await message.answer(text)


def setup(r: Router):
    r.message.register(
        list_of_commands,
        Command(commands='list')
    )
