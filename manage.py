from bot_config import bot, schedule, admins
from handlers import tasks, braintrash, hello, bomber, reminder, wiki
from handlers import road_to_the_dream as road
from handlers import text_to_speech as tts
from utils import log, notify

handlers = {
    'add_task': tasks.add,
    'trash': braintrash.write,
    'start': hello.start,
    'bomber': bomber.start,
    'add_remind': reminder.add,
    'road': road.start,
    'tts': tts.start,
    'wiki': wiki.search
}

admin_handlers = {
    'get_trash': braintrash.get_all_data,
    'get_log': log.get,
}


def start():
    bot.admins = admins
    bot.add_task(schedule.on_startup)
    for cmd in handlers:
        bot.add_command_handler(cmd, handlers[cmd])
    for cmd in admin_handlers:
        bot.add_command_handler(cmd, admin_handlers[cmd], admin_only=True)
    notify.notify_admins('bot started')
    bot.start()
    notify.notify_admins('bot stopped')
