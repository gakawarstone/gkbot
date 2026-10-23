from typing import ClassVar
import asyncio
from io import BytesIO
from pathlib import Path

import edge_tts
from gtts import gTTS

from services.cache_dir import CacheDir
from services.tts.entities import TTSProvider, TTSProviderType
from utils.async_cleanup import wait_for_completion


class EdgeTTSProvider(TTSProvider):
    VOICES: ClassVar[dict[str, str]] = {
        "ru": "ru-RU-DmitryNeural",
        "en": "en-US-AriaNeural",
    }

    async def synthesize(self, text: str, voice: str = "ru") -> bytes:
        voice_name = self.VOICES.get(voice, self.VOICES["ru"])
        communicate = edge_tts.Communicate(text, voice_name)
        cache_dir = CacheDir()
        try:
            output_file_path = cache_dir.get_file_path("tts.mp3")
            await communicate.save(output_file_path)
            return await wait_for_completion(
                asyncio.to_thread(Path(output_file_path).read_bytes)
            )
        finally:
            cache_dir.delete()


class GTTSProvider(TTSProvider):
    async def synthesize(self, text: str, voice: str = "ru") -> bytes:
        lang_map = {"ru": "ru", "en": "en"}
        lang = lang_map.get(voice, "ru")
        tts = gTTS(text=text, lang=lang)
        voice_file = BytesIO()
        await asyncio.to_thread(tts.write_to_fp, voice_file)
        return voice_file.getvalue()


PROVIDERS: dict[TTSProviderType, type[TTSProvider]] = {
    TTSProviderType.EDGE: EdgeTTSProvider,
    TTSProviderType.GTTS: GTTSProvider,
}
