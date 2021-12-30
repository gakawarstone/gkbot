from bot_config import bot
from modules import tasks, braintrash, hello, bomber, log

handlers = {
    'add_row': tasks.add_row,
    'trash': braintrash.write,
    'start': hello.start,
    'bomber': bomber.start
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
