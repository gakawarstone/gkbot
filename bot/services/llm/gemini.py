from typing import AsyncGenerator

from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel

from configs.env import GEMINI_API_KEY
from ._base import LLM


class Gemini(LLM):
    @classmethod
    def _get_model(cls) -> GenerativeModel:
        configure(api_key=GEMINI_API_KEY)
        return GenerativeModel("gemini-2.0-flash")

    @classmethod
    async def generate(cls, prompt: str) -> str:
        response = await cls._get_model().generate_content_async(prompt)
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        return ""

    @classmethod
    async def stream(cls, prompt: str, *args) -> AsyncGenerator[str, None]:
        response_stream = await cls._get_model().generate_content_async(
            prompt, stream=True
        )
        async for chunk in response_stream:
            if chunk.candidates and chunk.candidates[0].content.parts:
                for part in chunk.candidates[0].content.parts:
                    if hasattr(part, "text"):
                        yield part.text
