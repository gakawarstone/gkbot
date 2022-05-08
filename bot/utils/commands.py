import logging
from aiogram import Dispatcher
from aiogram import types

logger = logging.getLogger(__name__)


class DefaultCommands:
    commands = []

    @classmethod
    def set(cls, commands: dict[str, str]):
        for cmd in commands:
            cls.commands.append(types.BotCommand(cmd, commands[cmd]))
        return cls

    @classmethod
    async def on_startup(cls, dp: Dispatcher):
        logger.info('Setting bot commands\n' + str(cls.commands))
        await dp.bot.set_my_commands(cls.commands)
