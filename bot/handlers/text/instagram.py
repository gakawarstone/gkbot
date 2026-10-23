from collections.abc import Sequence
from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InputMediaPhoto, InputMediaVideo, MediaUnion, Message

from extensions.handlers.message.base import BaseHandler
from services.instagram import InstagramDownloadError, InstagramService


class InstagramPostDownloadHandler(BaseHandler):
    async def handle(self) -> None:
        await self.event.delete()
        text = self.event.text or ""

        if not text:
            await self.event.answer("Не удалось распознать ссылку на пост Instagram")
            return

        status_message = await self.event.answer(f"Скачиваю {text}")
        await self.bot.send_chat_action(self.event.chat.id, "upload_photo")
        try:
            photos = await InstagramService.get_photos_album(text)
        except InstagramDownloadError:
            await status_message.edit_text(f"Не получилось скачать {text}")
            return

        await self._send_media(photos, status_message)

    async def _send_media(
        self,
        media: Sequence[InputMediaPhoto | InputMediaVideo],
        status_message: Message,
    ) -> None:
        if len(media) == 1:
            try:
                await status_message.edit_media(media[0])
                return
            except TelegramAPIError:
                # The status may no longer exist or may not be editable.
                pass

        for start in range(0, len(media), 10):
            album: list[MediaUnion] = list(media[start : start + 10])
            if len(album) == 1:
                await self._send_single_media(media[start])
            else:
                await self.bot.send_media_group(self.event.chat.id, album)

        # Delivery succeeded even if Telegram refuses to remove the status.
        with suppress(TelegramAPIError):
            await status_message.delete()

    async def _send_single_media(
        self, media: InputMediaPhoto | InputMediaVideo
    ) -> None:
        if isinstance(media, InputMediaVideo):
            await self.event.answer_video(
                media.media,
                thumbnail=media.thumbnail,
                cover=media.cover,
                start_timestamp=media.start_timestamp,
                width=media.width,
                height=media.height,
                duration=media.duration,
                supports_streaming=media.supports_streaming,
                caption=media.caption,
                parse_mode=media.parse_mode,
                caption_entities=media.caption_entities,
                show_caption_above_media=media.show_caption_above_media,
                has_spoiler=media.has_spoiler,
            )
        else:
            await self.event.answer_photo(
                media.media,
                caption=media.caption,
                parse_mode=media.parse_mode,
                caption_entities=media.caption_entities,
                show_caption_above_media=media.show_caption_above_media,
                has_spoiler=media.has_spoiler,
            )


def setup(r: Router) -> None:
    r.message.register(
        InstagramPostDownloadHandler, F.text.startswith("https://www.instagram.com/p/")
    )
