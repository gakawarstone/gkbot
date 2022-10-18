from datetime import datetime
import asyncio

from aiogram.types import Message


class Timer:
    def __init__(self, message: Message, seconds: int,
                 text: str = 'Start', delay: int = 1,
                 format_: str = '%M:%S') -> None:
        self.__message = message
        self.__duration = seconds
        self.__text = text
        self.__delay = delay
        self.__format = format_
        self.__finish_time: float

    @property
    def __now(self) -> float:
        return datetime.now().timestamp()

    @property
    def __remain_time(self) -> float:
        return self.__finish_time - self.__now

    def __render_remain_time(self) -> str:
        return self.__text + ' <b>%s</b>' % datetime.fromtimestamp(
            self.__remain_time).strftime(self.__format)

    async def run(self):
        msg = await self.__message.answer(self.__text)
        self.__finish_time = self.__now + self.__duration
        while True:
            if self.__now >= self.__finish_time:
                break
            await msg.edit_text(self.__render_remain_time())
            await asyncio.sleep(self.__delay)
        await msg.delete()
