from bot_config import bot
import aiogram
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
import asyncio


async def start(message: aiogram.types.Message):
    await message.answer('Вы включили бомбер')
    await message.answer('Надеемся вы понимате что вы делаете')
    await message.answer('Итак кто будет жертвой?')
    bot.add_state_handler(Form.spam_it_state, spam)
    await Form.spam_it_state.set()


async def spam(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    text = message.text
    if text.startswith('@'):
        for i in range(10):
            msg = await message.answer(text)
            await asyncio.sleep(5)
            await msg.delete()
    else:
        await message.answer('Призыв должен начинатся с @ [@ivanzolo2004]')
        await Form.spam_it_state.set()


class Form(StatesGroup):
    spam_it_state = State()
