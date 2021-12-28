from lib.bot import Bot
import lib.page
import os

# VARS
IN_HEROKU = os.environ.get('IN_HEROKU')
if IN_HEROKU:
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
else:
    import env
    BOT_TOKEN = env.BOT_TOKEN
    NOTION_TOKEN = env.NOTION_TOKEN

# main objects
bot = Bot(BOT_TOKEN)

# notion classes
Page = lib.page.Page
Database = lib.page.Database
