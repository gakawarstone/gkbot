"""Temporary status messages with an ordinary-message fallback."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from aiogram.enums import ChatType
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import CallbackQuery, EphemeralMessageParameters, Message

logger = logging.getLogger(__name__)


@dataclass
class StatusMessage:
    _message: Message
    _receiver_user_id: int | None = None
    _deleted: bool = field(default=False, init=False)
    _keep: bool = field(default=False, init=False)

    async def edit_text(self, text: str) -> None:
        if self._message.ephemeral_message_id is None:
            await self._message.edit_text(text)
        else:
            assert self._receiver_user_id is not None
            bot = self._message.bot
            assert bot is not None
            await bot.edit_ephemeral_message_text(
                chat_id=self._message.chat.id,
                receiver_user_id=self._receiver_user_id,
                ephemeral_message_id=self._message.ephemeral_message_id,
                text=text,
            )

    async def delete(self) -> None:
        """Best-effort cleanup must not hide a download error or cancellation."""
        if self._deleted:
            return
        try:
            if self._message.ephemeral_message_id is None:
                await self._message.delete()
            else:
                assert self._receiver_user_id is not None
                bot = self._message.bot
                assert bot is not None
                await bot.delete_ephemeral_message(
                    chat_id=self._message.chat.id,
                    receiver_user_id=self._receiver_user_id,
                    ephemeral_message_id=self._message.ephemeral_message_id,
                )
        except TelegramAPIError:
            logger.warning("Could not delete temporary status message", exc_info=True)
        else:
            self._deleted = True

    def keep(self) -> None:
        """Preserve an error notice, matching the ordinary-message behavior."""
        self._keep = True

    async def publish(self, text: str) -> Message:
        """Turn a waiting notice into a persistent generation response."""
        if self._message.ephemeral_message_id is None:
            await self._message.edit_text(text)
            self.keep()
            return self._message
        await self.delete()
        return await self._message.answer(text)


async def send_status(
    message: Message,
    text: str,
    *,
    callback: CallbackQuery | None = None,
    reuse_message: bool = False,
) -> StatusMessage:
    user = callback.from_user if callback else message.from_user
    if (
        message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}
        and user is not None
        and not user.is_bot
        and (callback is not None or message.sender_chat is None)
    ):
        try:
            response = await message.answer(
                text,
                ephemeral_message_parameters=EphemeralMessageParameters(
                    receiver_user_id=user.id,
                    callback_query_id=callback.id if callback else None,
                ),
                # Bot API 10.2 uses these fields; 10.3 uses the object above.
                receiver_user_id=user.id,
                callback_query_id=callback.id if callback else None,
            )
        except TelegramBadRequest as error:
            description = error.message.lower()
            if not any(
                marker in description
                for marker in (
                    "ephemeral",
                    "receiver_user",
                    "callback_query",
                    "query is too old",
                    "bot is not an administrator",
                    "chat_admin_required",
                )
            ):
                raise
        else:
            # Old servers may ignore unknown fields and return a normal Message.
            return StatusMessage(response, user.id)

    if reuse_message:
        status = StatusMessage(message, user.id if user else None)
        await status.edit_text(text)
        return status
    return StatusMessage(await message.answer(text))


@asynccontextmanager
async def temporary_status(
    message: Message,
    text: str,
    *,
    callback: CallbackQuery | None = None,
    reuse_message: bool = False,
) -> AsyncIterator[StatusMessage]:
    status = await send_status(
        message, text, callback=callback, reuse_message=reuse_message
    )
    try:
        yield status
    finally:
        if not status._keep:
            await status.delete()
