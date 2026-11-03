from aiogram import Bot, Router
from aiogram.enums import ChatType
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from configs.commands import USER_COMMANDS


async def create_topic(message: Message, bot: Bot, command: CommandObject) -> None:
    async def respond(text: str) -> None:
        request = message.answer(text)
        request.message_thread_id = message.message_thread_id
        await request

    if (
        message.chat.type != ChatType.PRIVATE
        or message.chat.is_direct_messages
        or message.business_connection_id
    ):
        await respond(
            "Команда /topic работает только в личном чате с ботом. Используй /chat для AI-чата."
        )
        return
    name = (command.args or "").strip() or "AI-чат"
    if len(name) > 128:
        await respond("Название темы должно содержать от 1 до 128 символов.")
        return
    try:
        if not (await bot.get_me()).has_topics_enabled:
            await respond(
                "Темы в личном чате сейчас недоступны. Используй /chat для обычного AI-чата."
            )
            return
        topic = await bot.create_forum_topic(chat_id=message.chat.id, name=name)
    except (TelegramNetworkError, TelegramRetryAfter):
        await respond(
            "Не удалось подтвердить создание темы. Проверь список тем перед повтором команды."
        )
        return
    except TelegramAPIError:
        await respond(
            "Не удалось создать тему. Темы могут быть недоступны. Используй /chat для обычного AI-чата."
        )
        return
    try:
        await bot.send_message(
            chat_id=message.chat.id,
            message_thread_id=topic.message_thread_id,
            text="Отправь /chat, чтобы начать отдельный AI-диалог в этой теме. /exit завершает режим только здесь.",
        )
    except TelegramAPIError:
        await respond(
            "Тема создана, но приветствие не отправлено. Открой её и отправь /chat."
        )


def setup(router: Router) -> None:
    router.message.register(create_topic, Command(USER_COMMANDS.topic))
