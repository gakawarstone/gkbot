from notion.client import NotionClient
from datetime import datetime
import config

client = NotionClient(config.TOKEN)

page = client.get_block("https://www.notion.so/gakawarstone/EL-DEDE-98997f76b28d48cb946d04e32b540e64")

cv = client.get_collection_view("https://www.notion.so/gakawarstone/67f38400c29f4137ac285fe6569567e2?v=d7e870b67e4b4becb65132a814f8f7af")
row = cv.collection.add_row()
row.name = "Старый испанский монах"
row.subject = "C#"
row.deadline = datetime(2021, 10, 31, 17, 2)
row.status = "Не начато"


def main():
    pass


if __name__ == "__main__":
    main()
