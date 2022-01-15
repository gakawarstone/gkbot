import aiogram
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from bot_config import bot
from root import NotionPage
Page = NotionPage
braintrash = Page('98997f76b28d48cb946d04e32b540e64')


async def write(message: aiogram.types.Message):
    await message.answer('Вы попали в свалку')
    await message.answer('Можете написать сюда все что захотите')
    bot.add_state_handler(Form.mes_handle, send_message)
    await Form.mes_handle.set()


async def get_all_data(message: aiogram.types.Message):
    await message.answer('Вывод всего что находится в свалке')
    for i, title in enumerate(await braintrash.get_all_children_titles()):
        outp = str(i + 1) + ': ' + title + ('\n' * 2)
        await message.answer(outp)


async def send_message(message: aiogram.types.Message, state: FSMContext):
    await braintrash.write(message.text)
    btn = bot.add_url_button(await braintrash.get_url(), text='Ссылка')
    await message.answer('Информация сохранена', reply_markup=btn)
    await state.finish()


class Form(StatesGroup):
    mes_handle = State()
