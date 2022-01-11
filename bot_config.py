from lib.bot import Bot
from lib.schedule import Schedule
from notion.client import NotionClient
import os

# VARS
IN_HEROKU = os.environ.get('IN_HEROKU')
if IN_HEROKU:
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
    NOTION_API_TOKEN = os.environ.get('NOTION_API_TOKEN')
    # Heroku PostgreSQL server
    DATABASE_URL = os.environ.get('DATABASE_URL')
else:
    import env
    BOT_TOKEN = env.BOT_TOKEN
    NOTION_TOKEN = env.NOTION_TOKEN
    NOTION_API_TOKEN = env.NOTION_API_TOKEN

# main objects
bot = Bot(BOT_TOKEN)
client = NotionClient(NOTION_TOKEN)
schedule = Schedule()
