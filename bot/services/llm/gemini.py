from typing import AsyncGenerator, Optional

from google import genai

from configs.env import GEMINI_API_KEY
from ._base import LLM, StreamChunk


class Gemini(LLM):
    def _get_client(self) -> genai.Client:
        return genai.Client(api_key=GEMINI_API_KEY)

    async def generate(self, prompt: str) -> str:
        client = self._get_client()
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return response.text or ""

    async def stream(
        self, prompt: str, images: Optional[list[str]] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        client = self._get_client()
        response_stream = await client.aio.models.generate_content_stream(
            model="gemini-2.5-flash", contents=prompt
        )
        async for chunk in response_stream:
            if chunk.text:
                yield StreamChunk(chunk.text, "content")
