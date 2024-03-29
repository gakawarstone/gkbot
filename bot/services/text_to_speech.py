from io import BytesIO

import gtts


class TextToSpeechService:
    @classmethod
    async def convert_text_to_speech(cls, text: str) -> bytes:
        gtts.gTTS(text=text, lang="ru").write_to_fp(voice_file := BytesIO())
        return voice_file.getvalue()
