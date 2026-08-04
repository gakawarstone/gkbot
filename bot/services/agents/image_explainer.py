import base64
from collections.abc import AsyncGenerator

from services.llm import OpenRouter


class ImageExplainer:
    @classmethod
    async def explain(cls, image: bytes) -> AsyncGenerator[str]:
        image_base64 = base64.b64encode(image).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{image_base64}"

        async for ch in OpenRouter().stream(
            """Что на этом изображении?
                (
                    отвечай сплошным текстом 
                    можешь использовать только выделение жирным <b></b>
                    италик не используй
                )
            """,
            [image_data_url],
        ):
            yield ch.text
