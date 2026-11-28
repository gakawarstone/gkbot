import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from services.http import HttpService
from services.litterbox import LitterboxUploader


class StaticFile:
    def __init__(self, path: str, cache: bool = True) -> None:
        self.__path = path
        self.__should_cache = cache
        self.__cache_url = ""
        self.__cache_expire_timestamp = 0.0

    @property
    def path(self) -> str:
        return self.__path

    async def get_cached_url(self) -> str | None:
        if not self.__should_cache:
            return None
        if datetime.now().timestamp() > self.__cache_expire_timestamp:
            self.__cache_url = await LitterboxUploader.upload_with_path(self.__path)
            self.__cache_expire_timestamp = (
                datetime.now() + timedelta(hours=1)
            ).timestamp()
        return self.__cache_url

    async def as_str(self) -> str:
        url = await self.get_cached_url()
        if url is None:
            return (await asyncio.to_thread(Path(self.__path).read_bytes)).decode(
                "utf-8"
            )
        return (await HttpService.get(url)).decode("utf-8")
