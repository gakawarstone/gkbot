import base64
from collections.abc import AsyncGenerator

from services.llm import OpenRouter


class ImageExplainer:
    @classmethod
    async def explain(
        cls, image: bytes, *, response_instructions: str = ""
    ) -> AsyncGenerator[str]:
        image_base64 = base64.b64encode(image).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{image_base64}"
        prompt = "Что на этом изображении?"
        if response_instructions:
            prompt = f"{prompt}\n{response_instructions}"

        async for chunk in OpenRouter().stream(prompt, [image_data_url]):
            yield chunk.text
