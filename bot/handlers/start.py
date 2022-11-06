from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from settings import USER_COMMANDS
# [ ] delete(move to menu)


async def start(message: Message):
    await message.answer('Приветствую тебя!')
    await message.answer('Чем займемся?')


def setup(r: Router):
    r.message.register(start, Command(commands=USER_COMMANDS.start))
