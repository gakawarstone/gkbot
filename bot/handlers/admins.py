import aiogram

from settings import bot

# BUG there is no admins in private chat


async def tag_all_admins(message: aiogram.types.Message):
    chat_admins = await bot.dp.bot.get_chat_administrators(message.chat.id)
    text = ''
    for admin in chat_admins:
        text += f'@{admin.user.username} '
    await message.answer(text)
