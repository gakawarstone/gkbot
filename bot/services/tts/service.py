from services.tts.entities import TTSProviderType
from services.tts.providers import PROVIDERS, EdgeTTSProvider


class TextToSpeechService:
    @classmethod
    async def convert_text_to_speech(
        cls,
        text: str,
        *,
        provider: TTSProviderType,
        voice: str = "ru",
    ) -> bytes:
        provider_class = PROVIDERS.get(provider, EdgeTTSProvider)
        provider_instance = provider_class()
        return await provider_instance.synthesize(text, voice)
