import os
import logging
import logging.config

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lib.bot import Bot
from lib.schedule import Schedule
from services.shiki import UserUpdatesDispatcher
from utils.commands import DefaultCommands


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
bot = Bot(BOT_TOKEN)
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
schedule = Schedule()


ADMINS = [
    897651738
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
    DefaultCommands.set(DEFAULT_COMMANDS).on_startup,
    schedule.on_startup,
    UserUpdatesDispatcher().on_startup,
]
