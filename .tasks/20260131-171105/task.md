# Task: instagram feed item view

## Plan
1.  **Analyze the current logic**: The `ShowFeedItemsHandler` is being modified to handle Instagram items specifically or at least differently (removing type check, filtering in service).
2.  **Refine `GkfeedService`**: The diff shows filtering for Instagram links (`instagram.com`, `www.instagram.com`). Ensure this logic is robust and integrated correctly.
3.  **Update Handlers**: `ShowFeedItemsHandler` modification to allow non-Message events or handle deletion differently needs review.
4.  **Fix/Update Tests**: The test `bot/tests/handlers/test_feed.py` is being updated to mock `GkfeedService` correctly and test with specific links (Spotify in the diff, but the task is about Instagram). Ensure tests cover the Instagram case.
5.  **New Files**: `InstagramFeedItemView` and its test are introduced. Ensure they are properly integrated and tested.

## Current Diff
```diff
diff --git a/bot/modules/feed/handlers/messages.py b/bot/modules/feed/handlers/messages.py
index 467f3d6..6f79f53 100644
--- a/bot/modules/feed/handlers/messages.py
+++ b/bot/modules/feed/handlers/messages.py
@@ -1,21 +1,16 @@
 import asyncio
 from typing import Any
 
-from aiogram.types import Message
-
-
 from ._base import BaseHandler
 from ._item_processor import GkfeedItemProcessorExtension
 
 
-class ShowFeedItemsHandler(
-    GkfeedItemProcessorExtension, BaseHandler
-):
+class ShowFeedItemsHandler(GkfeedItemProcessorExtension, BaseHandler):
     _items_limit = 1
 
     async def handle(self) -> Any:
-        if not isinstance(self.event, Message):
-            raise ValueError("event must be Message")
+        # if not isinstance(self.event, Message):
+        #     raise ValueError("event must be Message")
 
         await self.event.delete()
 
diff --git a/bot/services/gkfeed.py b/bot/services/gkfeed.py
index ae39a20..0a7668e 100644
--- a/bot/services/gkfeed.py
+++ b/bot/services/gkfeed.py
@@ -35,6 +35,12 @@ class GkfeedService:
                 print(raw_item)
                 continue
 
+            if not raw_item["link"].startswith(
+                ("https://instagram.com", "https://www.instagram.com")
+            ):
+                # print(raw_item)
+                continue
+
             item = self._convert_raw_data_to_feed_item(raw_item)
             if self._should_return_item_using_pocket_strategy(item):
                 yield item
diff --git a/bot/tests/handlers/test_feed.py b/bot/tests/handlers/test_feed.py
index d119792..54c943e 100644
--- a/bot/tests/handlers/test_feed.py
+++ b/bot/tests/handlers/test_feed.py
@@ -2,19 +2,27 @@ from typing import AsyncGenerator, override
 
 import pytest
 
-from services.gkfeed import FeedItem
+from services.gkfeed import FeedItem, GkfeedService
 from modules.feed import ShowFeedItemsHandler
 from .. import integration_test
 from . import Bot, Event
 
 
-class GkfeedService:
+class MockedGkfeedService(GkfeedService):
+    def __init__(self):
+        super().__init__("test_login", "test_password")
+
     async def get_all_user_items(self) -> AsyncGenerator[FeedItem, None]:
         links = [
-            "https://trashbox.ru/link/2025-03-10-iphone-17-air-iphone-17-pro",
-            "https://www.piokok.com/post/6733377018605557242512/",
-            "https://www.youtube.com/watch?v=5WMmPoHbQOo",
-            "https://ranobe.me/ranobe24/6117",
+            "https://open.spotify.com/album/31Q0RTl2JFPyexVMgwub3B",
+            # "https://vk.com/wall-158544627_190654",
+            # "https://vk.com/wall-219252372_40900",
+            # "https://www.hltv.org/matches/2387379/pain-vs-spirit-iem-chengdu-2025"
+            # "https://discours.io/articles/chapters/experience-changes-the-language"
+            # "https://trashbox.ru/link/2025-03-10-iphone-17-air-iphone-17-pro",
+            # "https://www.piokok.com/post/6733377018605557242512/",
+            # "https://www.youtube.com/watch?v=5WMmPoHbQOo",
+            # "https://ranobe.me/ranobe24/6117",
         ]
 
         for i, link in enumerate(links):
@@ -22,7 +30,9 @@ class GkfeedService:
 
 
 class MockedHandler(ShowFeedItemsHandler):
-    _gkfeed = GkfeedService()
+    @override
+    async def _gkfeed(self) -> GkfeedService:
+        return MockedGkfeedService()
 
     @property  # type: ignore[override]
     @override
@@ -34,4 +44,3 @@ class MockedHandler(ShowFeedItemsHandler):
 @pytest.mark.asyncio(loop_scope="session")
 async def test_handler():
     await MockedHandler(event=Event(breakpoint_at_delete=False)).handle()  # type: ignore[arg-type]
-
```

## New Files

### bot/modules/feed/handlers/views/instagram.py
```python
import base64
from bs4 import BeautifulSoup, Tag
from aiogram.types import BufferedInputFile

from services.gkfeed import FeedItem
from ...ui.keyboards import FeedMarkup
from . import BaseFeedItemView
from .video import VideoFeedItemView


class InstagramFeedItemView(VideoFeedItemView, BaseFeedItemView):
    async def _process_instagram_item(self, item: FeedItem):
        data = await (await self._gkfeed()).get_raw_item_data(item.id)
        item_data = data.get("item", {})
        text = item_data.get("text") or item_data.get("description") or ""
        print("len text: ", len(text))

        soup = BeautifulSoup(text, "html.parser")
        img_tag = soup.find("img")

        if not isinstance(img_tag, Tag):
            raise ValueError("No image tag found in the item content")

        src = img_tag.get("src")
        if not isinstance(src, str):
            raise ValueError("No src attribute found in the image tag")

        caption = item.title
        if caption:
            caption = caption.split("/")[-1].split(":")[1]

        if not src.startswith("data:image"):
            raise ValueError("Image src is not a base64 data URL")

        header, encoded = src.split(",", 1)
        extension = "jpg"
        if "png" in header:
            extension = "png"
        elif "gif" in header:
            extension = "gif"

        photo_data = base64.b64decode(encoded)
        photo = BufferedInputFile(photo_data, filename=f"image.{extension}")

        await self.answer_photo(
            photo,
            caption=caption,
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )
```

### bot/tests/handlers/test_instagram_view.py
```python
from typing import AsyncGenerator, override
from pathlib import Path
import pytest

from services.gkfeed import FeedItem, GkfeedService
from modules.feed import ShowFeedItemsHandler
from .. import integration_test
from . import Bot, Event


class MockedGkfeedService(GkfeedService):
    def __init__(self):
        super().__init__("test_login", "test_password")

    async def get_all_user_items(self) -> AsyncGenerator[FeedItem, None]:
        links = [
            "https://www.instagram.com/p/test_post_id",
        ]

        for i, link in enumerate(links):
            yield FeedItem(id=i + 1, title=f"link {i + 1}", feed_id=1, link=link)

    async def get_raw_item_data(self, item_id: int) -> dict:
        content = Path("test.html").read_text()
        return {"item": {"text": content}}


class MockedHandler(ShowFeedItemsHandler):
    @override
    async def _gkfeed(self) -> GkfeedService:
        return MockedGkfeedService()

    @property  # type: ignore[override]
    @override
    def bot(self) -> Bot:  # type: ignore[override]
        return Bot()


@integration_test
@pytest.mark.asyncio(loop_scope="session")
async def test_handler():
    await MockedHandler(event=Event(breakpoint_at_delete=False)).handle()  # type: ignore[arg-type]
```
