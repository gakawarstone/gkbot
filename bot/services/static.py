from datetime import datetime, timedelta
import asyncio
from pathlib import Path

from aiogram.types.input_file import FSInputFile, URLInputFile, InputFile

from configs.services.static import CACHE_STATIC_FILES
from services.litterbox import LitterboxUploader
from services.http import HttpService


class StaticFile:
    def __init__(self, path: str, cache: bool = True) -> None:
        self.__path = path
        self.__should_cache = cache
        self.__cache_url = ""
        self.__cache_expire_timestamp = 0.0

    @property
    async def _cache_url(self) -> str:
        if datetime.now().timestamp() > self.__cache_expire_timestamp:
            self.__cache_url = await LitterboxUploader.upload_with_path(self.__path)
            self.__cache_expire_timestamp = (
                datetime.now() + timedelta(hours=1)
            ).timestamp()
        return self.__cache_url

    async def as_str(self) -> str:
        if not self.__should_cache:
            return await asyncio.to_thread(
                Path(self.__path).read_text, encoding="utf-8"
            )
        return (await HttpService.get(await self._cache_url)).decode("utf-8")

    async def as_input_file(self) -> InputFile:
        if not CACHE_STATIC_FILES:
            return FSInputFile(self.__path)
        if not self.__should_cache:
            return FSInputFile(self.__path)
        return URLInputFile(await self._cache_url)
