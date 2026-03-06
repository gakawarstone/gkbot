import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.tts import TextToSpeechService, TTSProviderType


@pytest.mark.asyncio
async def test_convert_text_to_speech_edge():
    with patch("services.tts.providers.edge_tts.Communicate") as mock_communicate:
        mock_instance = MagicMock()
        mock_communicate.return_value = mock_instance
        mock_instance.save = AsyncMock()

        with patch("services.tts.providers.CacheDir") as mock_cache_dir:
            mock_cache_instance = MagicMock()
            mock_cache_dir.return_value = mock_cache_instance
            mock_cache_instance.get_file_path.return_value = "dummy.mp3"

            with patch(
                "builtins.open", patch("builtins.open", MagicMock()).start()
            ) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                mock_file.read.return_value = b"audio content"

                result = await TextToSpeechService.convert_text_to_speech(
                    "hello", provider=TTSProviderType.EDGE
                )

                assert result == b"audio content"
                mock_communicate.assert_called_once_with("hello", "ru-RU-DmitryNeural")


@pytest.mark.asyncio
async def test_convert_text_to_speech_gtts():
    with patch("services.tts.providers.GTTSProvider.synthesize") as mock_synthesize:
        mock_synthesize.return_value = b"gtts audio content"

        result = await TextToSpeechService.convert_text_to_speech(
            "hello", provider=TTSProviderType.GTTS
        )

        assert result == b"gtts audio content"
        mock_synthesize.assert_called_once_with("hello", "ru")


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("INTEGRATION_TEST") != "1", reason="Requires INTEGRATION_TEST=1"
)
async def test_convert_text_to_speech_edge_integration():
    # Real call to Edge TTS
    result = await TextToSpeechService.convert_text_to_speech(
        "Тест интеграции", provider=TTSProviderType.EDGE
    )

    assert isinstance(result, bytes)
    assert len(result) > 0
    # Check if it's likely an MP3 (should start with ID3 or have certain frames)
    # Edge TTS returns MP3
    assert result[:3] == b"ID3" or b"\xff" in result[:10]


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("INTEGRATION_TEST") != "1", reason="Requires INTEGRATION_TEST=1"
)
async def test_convert_text_to_speech_gtts_integration():
    # Real call to gTTS
    result = await TextToSpeechService.convert_text_to_speech(
        "Тест интеграции", provider=TTSProviderType.GTTS
    )

    assert isinstance(result, bytes)
    assert len(result) > 0
    # gTTS also returns MP3
    assert result[:3] == b"ID3" or b"\xff" in result[:10]
