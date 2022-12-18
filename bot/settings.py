import os
import logging
import logging.config

from dotenv import load_dotenv


# Logging config
logging.basicConfig(level=logging.WARNING,
                    format='%(name)s::%(levelname)s::%(message)s')
logger = logging.getLogger(__name__)


# Environmental variables
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
NOTION_API_TOKEN = os.getenv('NOTION_API_TOKEN')
DB_URL = os.getenv('DB_URL')
API_SERVER_URL = os.getenv('API_SERVER_URL')


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
    'books': 'personal book shelf',
    'platonus2indigo': 'convert test',
}
