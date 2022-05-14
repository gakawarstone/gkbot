import logging

import aiogram

logger = logging.getLogger(__name__)


async def echo_post(message: aiogram.types.Message):
    logger.info(
        f"""message from channel [{message.sender_chat.title}]: {message.text}"""
    )
    await message.answer("Привет от бота")
