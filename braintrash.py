import aiogram
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from bot_config import bot
import log
from page import Page
braintrash = Page('https://www.notion.so/gakawarstone/braintrash-98997f76b28d48cb946d04e32b540e64')


async def write(message: aiogram.types.Message):
    await message.answer('Вы попали в свалку')
    await message.answer('Можете написать сюда все что захотите')
    bot.add_state_handler(Form.mes_handle, send_message)
    await Form.mes_handle.set()


async def send_message(message: aiogram.types.Message, state: FSMContext):
    log.write(message.text)
    braintrash.write(message.text)
    await state.finish()


class Form(StatesGroup):
    mes_handle = State()
