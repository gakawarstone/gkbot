import asyncio

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from configs.commands import USER_COMMANDS


class FSM(StatesGroup):
    start = State()
    spam = State()
    finish = State()


async def start(message: Message, state: FSMContext):
    await state.set_state(FSM.spam)
    text = "Вы включили <b>💣 бомбер</b>. "
    text += "Надеемся вы понимаете что вы делаете. "
    text += "Итак кто будет <b>🧟‍♂️ жертвой</b>?"
    await message.answer(text)


async def spam(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    text = message.text
    if text and text.startswith("@"):
        for _ in range(10):
            msg = await message.answer(text)
            await asyncio.sleep(5)
            await msg.delete()
    else:
        await state.set_state(FSM.spam)
        await message.answer("Призыв должен начинаться с @ [@ivanzolo2004]")


def setup(r: Router):
    r.message.register(start, StateFilter(FSM.start))
    r.message.register(spam, StateFilter(FSM.spam))
    r.message.register(start, Command(commands=USER_COMMANDS.bomber))
