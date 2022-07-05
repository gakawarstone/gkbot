import logging
from aiogram import Dispatcher, Bot
from aiogram import types

logger = logging.getLogger(__name__)


class DefaultCommands:
    def __init__(self, bot: Bot) -> None:
        self.__bot = bot
        self.__commands = {}

    def set(self, commands: dict[str, str]):
        # for cmd in commands:
        #     self.commands.append(types.BotCommand(cmd, commands[cmd]))
        # return self
        self.commands = commands
        return self

    async def on_startup(self, dp: Dispatcher):
        logger.info('Setting bot commands\n' + str(self.commands))
        # await dp.bot.set_my_commands(self.commands)
        self.__bot.set_my_commands(
            [
                types.BotCommand(command=command, description=description)
                for command, description in self.commands.items()
            ]
        )
