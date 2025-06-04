from typing import Any, AsyncGenerator, Optional

from openai import AsyncOpenAI

from configs.env import OPENROUTER_API_KEY
from ._base import LLM


class OpenRouter(LLM):
    @classmethod
    async def stream(
        cls, prompt: str, images: Optional[list[str]] = None
    ) -> AsyncGenerator[str, None]:
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]

        if images:
            for image_url in images:
                content.append({"type": "image_url", "image_url": {"url": image_url}})

        completion = await client.chat.completions.create(
            model="meta-llama/llama-4-scout:free",
            messages=[{"role": "user", "content": content}],
            stream=True,
        )

        async for chunk in completion:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
