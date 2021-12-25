from bot_config import bot
import tasks
import log
import braintrash
import hello

handlers = {
    'add_row': tasks.add_row,
    'trash': braintrash.write,
    'get_trash': braintrash.get_all_data,
    'start': hello.start
}

admins = [
    897651738
]


def start():
    for command in handlers:
        bot.add_command_handler(command, handlers[command])
    bot.admins = admins
    bot.add_command_handler('get_log', log.get, admin_only=True)
    bot.start()
