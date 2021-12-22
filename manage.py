from bot_config import bot
import tasks
import log


def start():
    bot.add_command_handler('add_row', tasks.add_row)
    bot.add_command_handler('get_log', log.get)
    bot.start()
