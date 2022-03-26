import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lib.bot import Bot
from lib.schedule import Schedule

load_dotenv()

# VARS
BOT_TOKEN = os.environ.get('BOT_TOKEN')
NOTION_API_TOKEN = os.environ.get('NOTION_API_TOKEN')
DB_URL = os.environ.get('DB_URL')

# main objects
bot = Bot(BOT_TOKEN)
schedule = Schedule()
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

# config
admins = [
    897651738
]
