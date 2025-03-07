from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.filters.state import State, StateFilter, StatesGroup

from utils.chunks import split_str_into_chunks
from services.llm import Gemini
from ._commands import USER_COMMANDS


class FSM(StatesGroup):
    finish = State()
    get_response = State()


async def start_chat(message: Message, state: FSMContext):
    await state.set_state(FSM.get_response)
    await message.delete()
    await message.answer("Задайте свой вопрос 🤔")


async def get_response(message: Message, state: FSMContext):
    await state.set_state(FSM.finish)
    await message.delete()
    try:
        resp_text = await Gemini.generate(message.text)
        [await message.answer(ch) for ch in split_str_into_chunks(resp_text)]
    except Exception as e:
        await message.answer(
            "Извините, произошла ошибка при обработке вашего запроса 😔"
        )
        print(f"Error in chat handler: {str(e)}")


def setup(r: Router):
    r.message.register(start_chat, Command(commands=USER_COMMANDS.ask))
    r.message.register(get_response, StateFilter(FSM.get_response))
