from aiogram.types import Message
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncio

from lib.bot import BotManager


class FSM(StatesGroup):
    start = State()
    spam = State()
    finish = State()


async def start(message: Message, state: FSMContext):
    await state.set_state(FSM.spam)
    text = 'Вы включили <b>💣 бомбер</b>. '
    text += 'Надеемся вы понимаете что вы делаете. '
    text += 'Итак кто будет <b>🧟‍♂️ жертвой</b>?'
    await message.answer(text)


async def spam(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    text = message.text
    if text.startswith('@'):
        for i in range(10):
            msg = await message.answer(text)
            await asyncio.sleep(5)
            await msg.delete()
    else:
        await state.set_state(FSM.spam)
        await message.answer('Призыв должен начинаться с @ [@ivanzolo2004]')


def setup(mng: BotManager):
    mng.add_state_handler(FSM.start, start)
    mng.add_state_handler(FSM.spam, spam)
