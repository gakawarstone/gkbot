from abc import ABC, abstractmethod
from enum import Enum


class TTSProviderType(str, Enum):
    EDGE = "edge"
    GTTS = "gtts"


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice: str) -> bytes:
        pass
