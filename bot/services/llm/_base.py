from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any
import os


OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]


class LLM(ABC):
    @classmethod
    @abstractmethod
    async def generate(cls, prompt: str) -> str:
        pass

    @classmethod
    @abstractmethod
    async def stream(cls, prompt: str, *args: Any) -> AsyncGenerator[str, None]:
        pass
