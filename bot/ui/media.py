from collections.abc import AsyncGenerator
from contextlib import aclosing
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, URLInputFile

from services.cache_dir import ReadProtectedCacheDir


class _ReadProtectedInputFile(FSInputFile):
    async def read(self, bot: Bot) -> AsyncGenerator[bytes]:
        with ReadProtectedCacheDir.reading(Path(self.path)):
            async with aclosing(super().read(bot)) as chunks:
                async for chunk in chunks:
                    yield chunk


def media_input_file(
    file: Path | str, *, protect_from_cleanup: bool = False
) -> FSInputFile | URLInputFile:
    if isinstance(file, str):
        return URLInputFile(file)
    if protect_from_cleanup:
        return _ReadProtectedInputFile(file)
    return FSInputFile(file)
