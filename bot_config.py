import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lib.bot import Bot
from lib.DBapi import Local, PostgreSQL
from lib.schedule import Schedule

load_dotenv()

# VARS
IN_HEROKU = os.environ.get('IN_HEROKU')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
NOTION_API_TOKEN = os.environ.get('NOTION_API_TOKEN')

if IN_HEROKU:
    # Heroku PostgreSQL server
    DATABASE_URL = os.environ.get('DATABASE_URL')
    db = PostgreSQL(DATABASE_URL)
    engine = create_engine(DATABASE_URL)
else:
    LOCAL_DB_USER_PSWD = os.environ.get('LOCAL_DB_USER_PSWD').split()
    db_user = LOCAL_DB_USER_PSWD[0]
    db_password = LOCAL_DB_USER_PSWD[1]
    db = Local('bot', db_user, db_password)
    engine = create_engine(
        f'postgresql://{db_user}:{db_password}@localhost:5432/bot')

# main objects
bot = Bot(BOT_TOKEN)
schedule = Schedule()
Session = sessionmaker(bind=engine)

# config
admins = [
    897651738
]
