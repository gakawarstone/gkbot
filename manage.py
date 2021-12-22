from bot_config import bot
import tasks


def start():
    bot.add_command_handler('add_row', tasks.add_row)
    bot.start()
