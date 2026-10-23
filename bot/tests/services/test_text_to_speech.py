import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from services.cache_dir import CacheDir
from services.tts import TextToSpeechService, TTSProviderType


@pytest.mark.asyncio
async def test_convert_text_to_speech_edge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))

    async def save(path: str) -> None:
        Path(path).write_bytes(b"audio content")

    with patch("services.tts.providers.edge_tts.Communicate") as communicate:
        communicate.return_value.save = AsyncMock(side_effect=save)
        result = await TextToSpeechService.convert_text_to_speech(
            "hello", provider=TTSProviderType.EDGE
        )

    assert result == b"audio content"
    communicate.assert_called_once_with("hello", "ru-RU-DmitryNeural")
    communicate.return_value.save.assert_awaited_once()
    assert list(tmp_path.iterdir()) == []


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
    os.environ.get("INTEGRATION_TEST") != "1",
    reason="Requires INTEGRATION_TEST=1 and network access to Microsoft Edge TTS",
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
    os.environ.get("INTEGRATION_TEST") != "1",
    reason="Requires INTEGRATION_TEST=1 and network access to Google Translate TTS",
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


async def test_edge_failure_cleans_temporary_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(CacheDir, "_CacheDir__base_path", str(tmp_path))

    async def save(path: str) -> None:
        Path(path).write_bytes(b"partial")
        raise OSError("synthesis failed")

    with patch("services.tts.providers.edge_tts.Communicate") as communicate:
        communicate.return_value.save = AsyncMock(side_effect=save)
        with pytest.raises(OSError, match="synthesis failed"):
            await TextToSpeechService.convert_text_to_speech(
                "hello", provider=TTSProviderType.EDGE
            )
    assert list(tmp_path.iterdir()) == []
