import aiogram
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
import asyncio

from settings import bot


async def start(message: aiogram.types.Message):
    text = 'Вы включили <b>💣 бомбер</b>. '
    text += 'Надеемся вы понимаете что вы делаете. '
    text += 'Итак кто будет <b>🧟‍♂️ жертвой</b>?'
    await message.answer(text)
    bot.add_state_handler(FSM.spam, spam)
    await FSM.spam.set()


async def spam(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    text = message.text
    if text.startswith('@'):
        for i in range(10):
            msg = await message.answer(text)
            await asyncio.sleep(5)
            await msg.delete()
    else:
        await message.answer('Призыв должен начинаться с @ [@ivanzolo2004]')
        await FSM.spam.set()


class FSM(StatesGroup):
    spam = State()
