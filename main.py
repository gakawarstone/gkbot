from notion.client import NotionClient
from datetime import datetime
import config
from page import Page

client = NotionClient(config.TOKEN)

el_dede = Page("https://www.notion.so/gakawarstone/EL-DEDE-98997f76b28d48cb946d04e32b540e64")
print(el_dede.__get())



def main():
    pass


if __name__ == "__main__":
    main()
