import io

import aiogram
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
import gtts

from bot_config import bot


async def start(message: aiogram.types.Message):
    await message.answer('Привет это новая функция сделанная потомучто <b>могу</b>')
    await message.answer('Отправь мне сообщение и произойдет магия')
    bot.add_state_handler(FSM.msg_to_voice, msg_to_voice)
    await FSM.msg_to_voice.set()


async def msg_to_voice(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    voice_file = io.BytesIO()
    voice = gtts.gTTS(text=message.text, lang='ru')
    voice.write_to_fp(voice_file)
    await message.answer_audio(voice_file.getvalue(), title='Текст')


class FSM(StatesGroup):
    msg_to_voice = State()
