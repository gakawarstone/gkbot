from lib.bot import Bot
from lib.schedule import Schedule
import os
from dotenv import load_dotenv
load_dotenv()

# VARS
IN_HEROKU = os.environ.get('IN_HEROKU')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
NOTION_API_TOKEN = os.environ.get('NOTION_API_TOKEN')

if IN_HEROKU:
    # Heroku PostgreSQL server
    DATABASE_URL = os.environ.get('DATABASE_URL')
else:
    LOCAL_DB_USER_PSWD = os.environ.get('LOCAL_DB_USER_PSWD').split()

# main objects
bot = Bot(BOT_TOKEN)
schedule = Schedule()
