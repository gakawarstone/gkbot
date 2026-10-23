from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InputFile, Message

from services.video import VideoMetadata


async def send_video(
    sender: Callable[..., Awaitable[Message]],
    video: str | InputFile,
    *,
    metadata: VideoMetadata | None = None,
    **kwargs: Any,
) -> Message:
    """Retry rejected optional metadata once, keeping the original video args."""
    options = metadata.send_options(kwargs.get("duration")) if metadata else {}
    try:
        return await sender(video, **kwargs, **options)
    except TelegramBadRequest:
        if not options:
            raise
        # A public cover can expire or be rejected by Telegram. Older local
        # Bot API servers may also reject these optional fields altogether.
        return await sender(video, **kwargs)
