from notion.block import TextBlock
from notion_client import AsyncClient
from typing import Optional

from bot_config import NOTION_API_TOKEN
client = AsyncClient(auth=NOTION_API_TOKEN)


class Page(object):
    def __init__(self, url):
        self.id = url

    def get_url(self):
        return self.id

    def get_view(self, client=client):
        """get NotionClient object"""
        return client.get_block(self.id)

    def write(self, text):
        self.get_view().children.add_new(TextBlock, title=text)


class Database(Page):
    async def add_row(self, title: str) -> Page:
        properties = {
            "Name": {"title": [{"text": {"content": title}}]}
        }
        return await self.create_page(properties)

    async def create_page(self, properties: dict) -> Page:
        response = await client.pages.create(parent={"database_id": self.id},
                                             properties=properties)
        return Page(response['id'])

    async def get_data(self, filter: Optional[dict] = None) -> dict:
        if filter:
            return await client.databases.query(database_id=self.id,
                                                filter=filter)
        else:
            return await client.databases.query(database_id=self.id)
