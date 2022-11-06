import os
import logging
import logging.config

from dotenv import load_dotenv

from lib.commands import Commands
from lib.bot import BotManager
from lib.schedule import Schedule
from services.shiki.dispatcher import UserUpdatesDispatcher
from utils.commands import DefaultCommands
from utils.notify import Notifier
import models


# Logging config
logging.basicConfig(level=logging.WARNING,
                    format='%(name)s::%(levelname)s::%(message)s')
logger = logging.getLogger(__name__)


# Environmental variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
NOTION_API_TOKEN = os.getenv('NOTION_API_TOKEN')
DB_URL = os.getenv('DB_URL')

logger.info('BOT_TOKEN = ' + BOT_TOKEN)
logger.info('NOTION_API_TOKEN = ' + NOTION_API_TOKEN)
logger.info('DB_URL = ' + DB_URL)


# Main objects
mng = BotManager(BOT_TOKEN)


ADMINS = [
    897651738
]


MODELS = [
    'models.users',
    'models.road',
    'models.books',
    'models.timezone',
]


DEFAULT_COMMANDS = {
    'list': 'list of possible bot commands',
    'road': 'road to the dream',
    'bomber': 'use it for call someone',
    'add_remind': 'add remind',
    'start_timer': 'start timer',
    'admins': 'tag all admins',
}


TASKS_ON_STARTUP = [
    models.setup(DB_URL, MODELS),
    DefaultCommands(mng.bot).set(DEFAULT_COMMANDS),
    Schedule.on_startup(),
    UserUpdatesDispatcher.set_bot(mng.bot).on_startup(),
    Notifier.setup(mng.bot, ADMINS),
]


class _UserCommands(Commands):
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


USER_COMMANDS = _UserCommands()
