import logging
from aiogram import Bot
from aiogram.types import BotCommand

logger = logging.getLogger(__name__)


class DefaultCommands:
    def __init__(self, bot: Bot) -> None:
        self.__bot = bot

    def set(self, commands: dict[str, str]):
        self.commands = commands
        return self

    async def on_startup(self):
        logger.info('Setting bot commands\n' + str(self.commands))
        await self.__bot.set_my_commands(
            [
                BotCommand(command=command, description=description)
                for command, description in self.commands.items()
            ]
        )
