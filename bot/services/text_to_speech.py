import edge_tts

from services.cache_dir import CacheDir


# TODO: TTS Provider
# TODO: In options user can choose provider
# TODO: Return file path not bytes
class TextToSpeechService:
    @classmethod
    async def convert_text_to_speech(cls, text: str) -> bytes:
        # gtts.gTTS(text=text, lang="ru").write_to_fp(voice_file := BytesIO())
        # return voice_file.getvalue()
        cache_dir = CacheDir()
        VOICE = "ru-RU-DmitryNeural"
        communicate = edge_tts.Communicate(text, VOICE)
        output_file_path = cache_dir.get_file_path("test.mp3")
        await communicate.save(output_file_path)

        with open(output_file_path, "rb") as f:
            return f.read()
