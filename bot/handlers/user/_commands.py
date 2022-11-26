from lib.commands import Commands as _Commands


class _UserCommands(_Commands):
    add_tasks = 'add_tasks'
    trash = 'trash'
    start = 'start'
    bomber = 'bomber'
    add_remind = 'add_remind'
    tts = 'tts'
    wiki = 'wiki'
    shiki = 'shiki'
    sub = 'sub'
    list = 'list'
    road = 'road'
    get_trash = 'get_trash'
    books = 'books'
    start_timer = 'start_timer'


USER_COMMANDS = _UserCommands()
