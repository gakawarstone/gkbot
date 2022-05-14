import os
import os.path

if not os.path.isdir('logs'):
    os.mkdir('logs')

if not os.path.isfile('.env'):
    with open('.env', 'w') as file:
        print('Paste following data')
        token = input('Telegram bot token: ')
        file.write('BOT_TOKEN = ' + token + '\n')
        db_url = input('DB URL: ')
        file.write('DB_URL = ' + db_url + '\n')
        notion_api_token = input('Notion api token: ')
        file.write('NOTION_API_TOKEN = ' + notion_api_token + '\n')
    print('You can manually change it in .env file')
