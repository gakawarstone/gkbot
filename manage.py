from bot_config import bot
import tasks
import log
import braintrash
import hello

handlers = {
    'add_row': tasks.add_row,
    'get_log': log.get,
    'trash': braintrash.write,
    'start': hello.start
}


def start():
    for command in handlers:
        bot.add_command_handler(command, handlers[command])
    bot.start()
