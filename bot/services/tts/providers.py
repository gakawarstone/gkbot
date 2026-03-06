from typing import ClassVar

import edge_tts

from services.cache_dir import CacheDir
from services.tts.entities import TTSProvider, TTSProviderType


class EdgeTTSProvider(TTSProvider):
    VOICES: ClassVar[dict[str, str]] = {
        "ru": "ru-RU-DmitryNeural",
        "en": "en-US-AriaNeural",
    }

    async def synthesize(self, text: str, voice: str = "ru") -> bytes:
        voice_name = self.VOICES.get(voice, self.VOICES["ru"])
        communicate = edge_tts.Communicate(text, voice_name)
        cache_dir = CacheDir()
        output_file_path = cache_dir.get_file_path("tts.mp3")
        await communicate.save(output_file_path)

        with open(output_file_path, "rb") as f:
            return f.read()


class GTTSProvider(TTSProvider):
    async def synthesize(self, text: str, voice: str = "ru") -> bytes:
        from gtts import gTTS
        from io import BytesIO

        lang_map = {"ru": "ru", "en": "en"}
        lang = lang_map.get(voice, "ru")
        tts = gTTS(text=text, lang=lang)
        voice_file = BytesIO()
        tts.write_to_fp(voice_file)
        return voice_file.getvalue()


PROVIDERS: dict[TTSProviderType, type[TTSProvider]] = {
    TTSProviderType.EDGE: EdgeTTSProvider,
    TTSProviderType.GTTS: GTTSProvider,
}
