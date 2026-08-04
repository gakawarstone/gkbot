from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from configs.commands import USER_COMMANDS
from services.llm import OpenRouter


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

    if not message.text:
        raise ValueError("Prompt text is required")

    _message = await message.answer("Подождите..")
    text = ""
    async for ch in OpenRouter().stream(message.text):
        text += ch.text
        await _message.edit_text(text)


# TODO: inline @gkbot ai <prompt>
# FIXME: deprecated use /chatgpt
def setup(r: Router):
    r.message.register(start_chat, Command(commands=USER_COMMANDS.ask))
    r.message.register(get_response, StateFilter(FSM.get_response))
