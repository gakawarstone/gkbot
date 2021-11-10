from bot import Bot
import aiogram
import bot_config as c
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage


class Form(StatesGroup):
    """
    To add state use <obj>.states.append(State())
    """
    num_handle = State()


async def answer_it(message: aiogram.types.Message):
    if message["from"]["username"] == "Gakawarstone":
        await message.answer("ответь")
        print(message)


async def log_it(message: aiogram.types.Message):
    print(message)


async def sqr(message: aiogram.types.Message):
    if message["from"]["username"] == "Gakawarstone":
        await message.answer("Напиши число я возведу его в квадрат")
        await Form.num_handle.set()


async def get_number(message: aiogram.types.Message, state: FSMContext):
    if message["from"]["username"] == "Gakawarstone":
        async with state.proxy() as data:
            data['name'] = message.text
            x = int(data['name'])
            await message.answer(x ** 2)

    await state.finish()


bot = Bot(c.TOKEN)
bot.add_command_handler('sqr', sqr)
bot.add_state_handler(Form.num_handle, get_number)


bot.start()
