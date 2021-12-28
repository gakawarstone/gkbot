from bot_config import bot
import tasks
import log
import braintrash
import hello
import bomber

handlers = {
    'add_row': tasks.add_row,
    'trash': braintrash.write,
    'start': hello.start,
    'bomber': bomber.call
}

admin_handlers = {
    'get_trash': braintrash.get_all_data,
    'get_log': log.get
}

admins = [
    897651738
]


def start():
    bot.admins = admins
    for cmd in handlers:
        bot.add_command_handler(cmd, handlers[cmd])
    for cmd in admin_handlers:
        bot.add_command_handler(cmd, admin_handlers[cmd], admin_only=True)
    bot.start(on_startup=bot.on_startup)
