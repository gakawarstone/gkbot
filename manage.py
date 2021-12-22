from bot_config import bot
import tasks
import log
import braintrash

handlers = {
    'add_row': tasks.add_row,
    'get_log': log.get,
    'trash': braintrash.write
}


def start():
    for command in handlers:
        bot.add_command_handler(command, handlers[command])
    bot.start()
