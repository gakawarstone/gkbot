import logging
from aiogram import Bot
from aiogram.types import BotCommand

logger = logging.getLogger(__name__)


class DefaultCommands:
    def __init__(self, bot: Bot) -> None:
        self.__bot = bot

    async def set(self, commands: dict[str, str]):
        logger.info('Setting bot commands\n' + str(commands))
        await self.__bot.set_my_commands(
            [
                BotCommand(command=command, description=description)
                for command, description in commands.items()
            ]
        )
