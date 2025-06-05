from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any


class LLM(ABC):
    @classmethod
    @abstractmethod
    async def generate(cls, prompt: str) -> str:
        pass

    @classmethod
    @abstractmethod
    async def stream(cls, prompt: str, *args: Any) -> AsyncGenerator[str, None]:
        pass
