from typing import AsyncGenerator, Optional

from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel

from configs.env import GEMINI_API_KEY
from ._base import LLM, StreamChunk


class Gemini(LLM):
    def _get_model(self) -> GenerativeModel:
        configure(api_key=GEMINI_API_KEY)
        return GenerativeModel("gemini-2.5-flash")

    async def generate(self, prompt: str) -> str:
        response = await self._get_model().generate_content_async(prompt)
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        return ""

    async def stream(
        self, prompt: str, images: Optional[list[str]] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        response_stream = await self._get_model().generate_content_async(
            prompt, stream=True
        )
        async for chunk in response_stream:
            if chunk.candidates and chunk.candidates[0].content.parts:
                for part in chunk.candidates[0].content.parts:
                    if hasattr(part, "text"):
                        yield StreamChunk(part.text, "content")
