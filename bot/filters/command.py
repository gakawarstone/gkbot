from aiogram.filters import BaseFilter
from aiogram.types import Message


class CommandWithPrompt(BaseFilter):
    def __init__(self, command: str) -> None:
        self.command = command

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        return message.text.startswith(f"/{self.command} ")
