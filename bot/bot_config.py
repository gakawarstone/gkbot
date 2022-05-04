import os
import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lib.bot import Bot
from lib.schedule import Schedule

# logger configuration
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

load_dotenv()

# VARS
BOT_TOKEN = os.environ.get('BOT_TOKEN')
NOTION_API_TOKEN = os.environ.get('NOTION_API_TOKEN')
DB_URL = os.environ.get('DB_URL')

# Log info vars
logger.info('BOT_TOKEN = ' + BOT_TOKEN)
logger.info('NOTION_API_TOKEN = ' + NOTION_API_TOKEN)
logger.info('DB_URL = ' + DB_URL)

# main objects
bot = Bot(BOT_TOKEN)
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

# SINGLETON
schedule = Schedule()

# config
admins = [
    897651738
]
