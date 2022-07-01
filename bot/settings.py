# [ ] rename to settings.py
import os
import logging
import logging.config

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lib.bot import Bot
from lib.schedule import Schedule

# Logging config
logging.basicConfig(level=logging.WARNING,
                    format='%(name)s::%(levelname)s::%(message)s')
logger = logging.getLogger(__name__)

# Environmental variables
load_dotenv()

# VARS
BOT_TOKEN = os.getenv('BOT_TOKEN')
NOTION_API_TOKEN = os.getenv('NOTION_API_TOKEN')
DB_URL = os.getenv('DB_URL')

# Log info vars
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
