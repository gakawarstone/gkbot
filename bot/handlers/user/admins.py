from aiogram.types import Message
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.fsm.context import FSMContext

from lib.bot import BotManager

# BUG there is no admins in private chat


class FSM(StatesGroup):
    tag_all_admins = State()


async def tag_all_admins(message: Message, state: FSMContext):
    chat_admins = await state.bot.get_chat_administrators(message.chat.id)
    text = ''
    for admin in chat_admins:
        text += f'@{admin.user.username} '
    await message.answer(text)


def setup(mng: BotManager):
    mng.add_state_handler(FSM.tag_all_admins, tag_all_admins)
