import logging
from aiogram import Bot
from aiogram.types import BotCommand

logger = logging.getLogger(__name__)


class DefaultCommands:
    def __init__(self, commands: dict[str, str]) -> None:
        self.__commands = commands

    async def set(self, bot: Bot):
        logger.info('Setting bot commands\n' + str(self.__commands))
        await bot.set_my_commands(
            [
                BotCommand(command=command, description=description)
                for command, description in self.__commands.items()
            ]
        )
